from typing import Optional

from open_run_lab import vendor
from open_run_lab.converter.base import BaseConverter


class MLFlowConverter(BaseConverter):
    """Convert a single MLflow experiment to a OpenRunLab project.

    MLflow experiment → OpenRunLab project, MLflow run → OpenRunLab run.

    Example::

        mlf = MLFlowConverter(project="my-orlab-proj")
        mlf.run(tracking_uri="http://localhost:5000", experiment="my-experiment")
        mlf.run(tracking_uri="http://localhost:5000", experiment="my-experiment", run_id="abc123")
    """

    def run(  # type: ignore[override]
        self,
        tracking_uri: str,
        experiment: str,
        run_id: Optional[str] = None,
    ) -> None:
        mlflow = vendor.mlflow

        import open_run_lab
        from open_run_lab.vendor.mlflow.exceptions import MlflowException  # type: ignore

        client = mlflow.MlflowClient(tracking_uri=tracking_uri)

        try:
            ex = client.get_experiment(experiment)
        except MlflowException:
            ex = client.get_experiment_by_name(experiment)
        if not ex:
            raise ValueError(f'Could not find MLflow experiment with id or name "{experiment}"')

        runs = client.search_runs(ex.experiment_id)

        if run_id is not None:
            runs = [r for r in runs if r.info.run_id == run_id]
            if not runs:
                raise ValueError(f'Could not find MLflow run with id "{run_id}" in experiment "{ex.name}"')

        print(f'Experiment "{ex.name}" — {len(runs)} run(s) to convert.')

        for run in runs:
            mlflow_run_id = run.info.run_id
            mlflow_run_name = run.data.tags.get("mlflow.runName")
            description = run.data.tags.get("mlflow.note.content")
            orlab_run = open_run_lab.init(
                project=self.project or ex.name,
                workspace=self.workspace,
                mode=self.mode,  # type: ignore[arg-type]
                log_dir=self.log_dir,
                name=mlflow_run_name,
                description=description,
                reinit=True,
            )

            orlab_run.config.update(
                {
                    "mlflow_run_id": mlflow_run_id,
                    "mlflow_run_name": mlflow_run_name,
                    "mlflow_run_description": description,
                    "mlflow_run_params": run.data.params,
                    "mlflow_run_tags": {k: v for k, v in run.data.tags.items() if not k.startswith("mlflow.")},
                }
            )

            all_metric_histories = {}
            for key in run.data.metrics.keys():
                all_metric_histories[key] = client.get_metric_history(mlflow_run_id, key)

            total_metrics = sum(len(h) for h in all_metric_histories.values())
            print(f"  Converting run: {mlflow_run_name or mlflow_run_id[:8]} ({total_metrics} metrics)")

            for key, history in all_metric_histories.items():
                for m in history:
                    orlab_run.log({m.key: m.value}, step=m.step)

            orlab_run.finish()
            print(f"  ✓ Finished converting run: {mlflow_run_name or mlflow_run_id[:8]}")

        print("All MLflow runs converted successfully.")
