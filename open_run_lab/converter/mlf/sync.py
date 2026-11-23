import os

import open_run_lab
from open_run_lab import vendor
from open_run_lab.converter.helper import extract_args
from open_run_lab.sdk.typings.run import ModeType


def sync_mlflow(mode: ModeType = "offline") -> None:
    """Monkey-patch mlflow to forward logs to OpenRunLab.

    Call before any mlflow API usage.

    Args:
        mode: OpenRunLab mode — offline | disabled.

    Example::

        import open_run_lab
        open_run_lab.sync_mlflow()

        import mlflow
        mlflow.set_experiment("my_experiment")

        with mlflow.start_run(run_name="my_run"):
            mlflow.log_param("learning_rate", 0.01)
            for step in range(10):
                mlflow.log_metric("loss", 0.5 / (step + 1), step=step)

        mlflow.end_run()
    """
    mlflow = vendor.mlflow

    original_set_experiment = mlflow.set_experiment
    original_start_run = mlflow.start_run
    original_end_run = mlflow.end_run
    original_log_param = mlflow.log_param
    original_log_params = mlflow.log_params
    original_log_metric = mlflow.log_metric
    original_log_metrics = mlflow.log_metrics

    def patched_set_experiment(*args, **kwargs):
        experiment_name = extract_args(original_set_experiment, args, kwargs, ["experiment_name"])[0]
        if experiment_name and not open_run_lab.has_run():
            os.environ["ORLAB_MLFLOW_PROJECT"] = experiment_name
        return original_set_experiment(*args, **kwargs)

    def patched_start_run(*args, **kwargs):
        run_name = extract_args(original_start_run, args, kwargs, ["run_name"])[0]

        if not open_run_lab.has_run():
            project = os.environ.get("ORLAB_MLFLOW_PROJECT")
            open_run_lab.init(project=project, name=run_name, mode=mode)
        elif run_name:
            open_run_lab.config.update({"mlflow_run_name": run_name})

        return original_start_run(*args, **kwargs)

    def patched_end_run(*args, **kwargs):
        open_run_lab.finish()
        return original_end_run(*args, **kwargs)

    def patched_log_param(*args, **kwargs):
        key, value = extract_args(original_log_param, args, kwargs, ["key", "value"])
        if key is not None:
            open_run_lab.config.update({key: value})
        return original_log_param(*args, **kwargs)

    def patched_log_params(*args, **kwargs):
        params = extract_args(original_log_params, args, kwargs, ["params"])[0]
        if params:
            open_run_lab.config.update(params)
        return original_log_params(*args, **kwargs)

    def patched_log_metric(*args, **kwargs):
        key, value, step = extract_args(original_log_metric, args, kwargs, ["key", "value", "step"])
        if key is not None:
            open_run_lab.log({key: value}, step=step)
        return original_log_metric(*args, **kwargs)

    def patched_log_metrics(*args, **kwargs):
        metrics, step = extract_args(original_log_metrics, args, kwargs, ["metrics", "step"])
        if metrics:
            open_run_lab.log(metrics, step=step)
        return original_log_metrics(*args, **kwargs)

    mlflow.set_experiment = patched_set_experiment
    mlflow.start_run = patched_start_run
    mlflow.end_run = patched_end_run
    mlflow.log_param = patched_log_param
    mlflow.log_params = patched_log_params
    mlflow.log_metric = patched_log_metric
    mlflow.log_metrics = patched_log_metrics
