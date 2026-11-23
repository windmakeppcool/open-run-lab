"""
Public converter API — convert experiment logs from other tracking tools into OpenRunLab.

Usage::

    from open_run_lab.converter import WandbConverter

    wb = WandbConverter(
        project="my-project",   # optional OpenRunLab project name
        mode="offline",         # offline | disabled
    )
    wb.run(wb_project="WANDB_PROJECT", wb_entity="WANDB_ENTITY")

For local wandb files::

    from open_run_lab.converter import WandbLocalConverter

    wb = WandbLocalConverter(project="my-project")
    wb.run(root_wandb_dir="./wandb")

For TensorBoard::

    from open_run_lab.converter import TFBConverter

    tb_converter = TFBConverter(convert_dir="[TFEVENT_LOGDIR]")
    tb_converter.run()

For MLflow::

    from open_run_lab.converter import MLFlowConverter

    mlf = MLFlowConverter(project="my-project")
    # Optional: `experiment`
    mlf.run(tracking_uri="http://localhost:5000", experiment: Optional[str]="1")

Runtime sync (monkey-patch)::

    import open_run_lab
    open_run_lab.sync_wandb()           # intercept wandb calls → OpenRunLab

    import wandb
    wandb.init(project="test")
    wandb.log({"loss": 0.5})
    wandb.finish()

Or sync MLflow::

    import open_run_lab
    open_run_lab.sync_mlflow()

    import mlflow
    mlflow.set_experiment("my_experiment")
    with mlflow.start_run(run_name="my_run"):
        mlflow.log_metric("loss", 0.5, step=0)
"""

from open_run_lab.converter.mlf import MLFlowConverter
from open_run_lab.converter.mlf.sync import sync_mlflow
from open_run_lab.converter.tfb import TFBConverter
from open_run_lab.converter.tfb.sync import sync_tensorboard_torch, sync_tensorboardX
from open_run_lab.converter.wb import WandbConverter, WandbLocalConverter
from open_run_lab.converter.wb.sync import sync_wandb

__all__ = [
    "WandbConverter",
    "WandbLocalConverter",
    "TFBConverter",
    "MLFlowConverter",
    "sync_wandb",
    "sync_tensorboardX",
    "sync_tensorboard_torch",
    "sync_mlflow",
]
