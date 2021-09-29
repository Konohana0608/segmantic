from monai.config import print_config
import os
import typer
from pathlib import Path
from typing import List

from segmantic.prepro.labels import load_tissue_list
from segmantic.seg import monai_unet


def get_nifti_files(dir: Path) -> List[Path]:
    if not dir:
        return []
    return sorted([f for f in dir.glob("*.nii.gz")])


def main(
    image_dir: Path = typer.Option(
        ..., "--image_dir", "-i", help="directory containing images"
    ),
    labels_dir: Path = typer.Option(
        ..., "--labels_dir", "-l", help="directory containing labelfields"
    ),
    tissue_list: Path = typer.Option(
        ..., "--tissue_list", help="label descriptors in iSEG format"
    ),
    results_dir: Path = Path("results"),
    predict: bool = False,
    gpu_ids: List[int] = [0],
):
    """Train UNet or predict segmentation

    Example invocation:

        -i ./dataset/images -l ./dataset/labels --results_dir ./results --tissue_list ./dataset/labels.txt
    """

    print_config()

    tissue_dict = load_tissue_list(tissue_list)
    num_classes = max(tissue_dict.values()) + 1
    assert (
        len(tissue_dict) == num_classes
    ), "Expecting contiguous labels in range [0,N-1]"

    os.makedirs(results_dir, exist_ok=True)
    log_dir = Path(results_dir) / "logs"
    model_file = Path(results_dir) / ("drcmr_%d.ckpt" % num_classes)

    if predict:
        monai_unet.predict(
            model_file=model_file,
            test_images=get_nifti_files(image_dir),
            test_labels=get_nifti_files(labels_dir),
            tissue_dict=tissue_dict,
            output_dir=results_dir,
            save_nifti=True,
            gpu_ids=gpu_ids,
        )
    else:
        monai_unet.train(
            image_dir=image_dir,
            labels_dir=labels_dir,
            log_dir=log_dir,
            num_classes=num_classes,
            model_file_name=model_file,
            max_epochs=600,
            output_dir=results_dir,
            gpu_ids=gpu_ids,
        )


if __name__ == "__main__":
    typer.run(main)
