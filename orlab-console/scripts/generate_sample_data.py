"""生成 orlab-log 样例数据，供 orlab-console 前后端开发与测试使用。

用法（在 OpenRunLab 仓库根目录下）：
    PYTHONPATH=. ORLAB_LOGDIR=orlab-console/testdata/orlab-log python3 orlab-console/scripts/generate_sample_data.py

生成 5 个真实 run（均由 SDK 以 offline 模式写出）：
  1. qwen-lora-r16    正常结束（60 步标量 + 终端日志）
  2. qwen-lora-r8     正常结束
  3. resnet50-aug-v2  正常结束（含 Text 媒体记录）
  4. qwen-full-ft     异常崩溃（RuntimeError → CRASHED）
  5. bert-ner-e2e     进程被强杀（无 FinishRecord → RUNNING，尾部可能截断）
"""

import math
import os
import subprocess
import sys
import time


def scenario_qwen(name: str, lora_r: int, loss_base: float, acc_base: float) -> None:
    import open_run_lab

    run = open_run_lab.init(
        project="qwen-lora-sft",
        name=name,
        description=f"Qwen2.5-0.5B LoRA 微调基线，lora_r={lora_r}",
        tags=["lora", f"r{lora_r}", "qwen2"],
        group="qwen-lora",
        config={
            "learning_rate": 2e-4,
            "lora_r": lora_r,
            "lora_alpha": 32,
            "batch_size": 4,
            "epochs": 3,
            "optimizer": "adamw",
        },
        mode="offline",
    )
    for step in range(1, 61):
        run.log(
            {
                "train/loss": loss_base + 0.6 * math.exp(-step / 18) + 0.03 * math.sin(step / 3),
                "train/acc": acc_base + (1 - acc_base) * (1 - math.exp(-step / 22)) - 0.01 * math.sin(step / 4),
                "train/lr": 2e-4 * (1 - step / 60),
            },
            step=step,
        )
        if step % 10 == 0:
            run.log(
                {
                    "eval/loss": loss_base + 0.65 * math.exp(-step / 20) + 0.02,
                    "eval/acc": acc_base + (1 - acc_base) * (1 - math.exp(-step / 24)),
                },
                step=step,
            )
            print(f"[{name}] step={step} eval/loss={loss_base + 0.65 * math.exp(-step / 20) + 0.02:.4f}")
    run.finish()


def scenario_resnet() -> None:
    import open_run_lab

    run = open_run_lab.init(
        project="resnet-classifier",
        name="resnet50-aug-v2",
        description="ResNet50 猫狗分类，启用数据增强",
        tags=["resnet", "aug"],
        config={"learning_rate": 1e-3, "batch_size": 32, "image_size": 224, "augment": True},
        mode="offline",
    )
    for step in range(1, 41):
        run.log(
            {
                "train/loss": 1.2 + 0.9 * math.exp(-step / 12) + 0.04 * math.sin(step / 2),
                "train/acc": 0.55 + 0.4 * (1 - math.exp(-step / 14)),
                "val/acc": 0.52 + 0.42 * (1 - math.exp(-step / 16)),
            },
            step=step,
        )
        if step == 20:
            run.log({"samples/text": open_run_lab.Text("预测: cat | 真实: cat | 置信度: 0.94")}, step=step)
        if step % 10 == 0:
            print(f"[resnet50-aug-v2] step={step} val/acc={0.52 + 0.42 * (1 - math.exp(-step / 16)):.4f}")
    run.finish()


def scenario_crash() -> None:
    import open_run_lab

    run = open_run_lab.init(
        project="qwen-lora-sft",
        name="qwen-full-ft",
        description="Qwen2.5-0.5B 全量微调（显存不足中断）",
        tags=["full-ft", "qwen2"],
        config={"learning_rate": 5e-5, "batch_size": 16, "epochs": 3, "optimizer": "adamw"},
        mode="offline",
    )
    for step in range(1, 26):
        run.log(
            {"train/loss": 1.8 + 0.4 * math.exp(-step / 15), "train/acc": 0.3 + 0.15 * (1 - math.exp(-step / 15))},
            step=step,
        )
        print(f"[qwen-full-ft] step={step} train/loss={1.8 + 0.4 * math.exp(-step / 15):.4f}")
    raise RuntimeError("CUDA out of memory. Tried to allocate 2.50 GiB (GPU 0; 23.65 GiB total capacity)")


def scenario_running() -> None:
    import open_run_lab

    run = open_run_lab.init(
        project="bert-ner",
        name="bert-ner-e2e",
        description="BERT 命名实体识别端到端训练",
        tags=["bert", "ner"],
        config={"learning_rate": 3e-5, "batch_size": 16, "epochs": 5, "max_length": 256},
        mode="offline",
    )
    for step in range(1, 401):
        run.log(
            {
                "train/loss": 2.4 + 1.1 * math.exp(-step / 120) + 0.02 * math.sin(step / 9),
                "train/f1": 0.35 + 0.55 * (1 - math.exp(-step / 150)),
            },
            step=step,
        )
        if step % 50 == 0:
            print(f"[bert-ner-e2e] step={step} running...")
    # 等待后台消费者把队列中的记录落盘，避免强杀时数据还堆在缓冲区里
    time.sleep(5)
    # 强杀进程：不触发任何收尾逻辑，模拟"仍在运行"的 run（无 FinishRecord）
    os._exit(1)


SCENARIOS = {
    "qwen-r16": lambda: scenario_qwen("qwen-lora-r16", 16, 1.42, 0.48),
    "qwen-r8": lambda: scenario_qwen("qwen-lora-r8", 8, 1.55, 0.42),
    "resnet": scenario_resnet,
    "crash": scenario_crash,
    "running": scenario_running,
}


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--scenario":
        SCENARIOS[sys.argv[2]]()
        return
    # 父进程：逐个拉起子进程执行各场景，保证崩溃/强杀行为是真实的进程级行为
    for key in SCENARIOS:
        print(f"generating scenario: {key} ...")
        ret = subprocess.run([sys.executable, os.path.abspath(__file__), "--scenario", key], env=os.environ.copy())
        if ret.returncode != 0 and key not in ("crash", "running"):
            raise SystemExit(f"scenario {key} failed with code {ret.returncode}")
    print("done.")


if __name__ == "__main__":
    main()
