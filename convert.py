import argparse
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import numpy as np
import tensorflow as tf
import torch
from tensorflow.keras import layers

from mobilevit.models import mobilevit
from mobilevit.models.mobilevit_pt import get_mobilevit_pt

torch.set_grad_enabled(False)

DATASET_TO_CLASSES = {
    "imagenet-1k": 1000,
}

TF_MODEL_ROOT = "saved_models"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Conversion of the PyTorch pre-trained MobileViT weights to TensorFlow."
    )
    parser.add_argument(
        "-d",
        "--dataset",
        default="imagenet-1k",
        type=str,
        required=False,
        choices=["imagenet-1k", "imagenet-21k"],
        help="Name of the dataset.",
    )
    parser.add_argument(
        "-m",
        "--model-name",
        default="mobilevit_xxs",
        type=str,
        required=False,
        choices=[
            "mobilevit_xxs",
            "mobilevit_xs",
            "mobilevit_s",
        ],
        help="Types of MobileViT models.",
    )
    parser.add_argument(
        "-r",
        "--image-resolution",
        default=256,
        type=int,
        required=False,
        help="Image resolution of the model.",
    )
    parser.add_argument(
        "-c",
        "--checkpoint-path",
        default="https://dl.fbaipublicfiles.com/convnext/convnext_tiny_1k_224_ema.pth",
        type=str,
        required=False,
        help="URL of the checkpoint to be loaded.",
    )
    return vars(parser.parse_args())


def main(args):
    print(f'Model: {args["model_name"]}')
    print(f'Image resolution: {args["image_resolution"]}')
    print(f'Dataset: {args["dataset"]}')
    print(f'Checkpoint URL: {args["checkpoint_path"]}')

    print("Instantiating PyTorch model and populating weights...")
    mobilevit_model_pt = get_mobilevit_pt(model_name=args["model_name"])
    mobilevit_model_pt.eval()  # run all component in inference mode

    print("Instantiating TensorFlow model...")
    mobilevit_model_tf = mobilevit.get_mobilevit_model(
        model_name=args["model_name"],
        image_shape=(args["image_resolution"], args["image_resolution"], 3),
        num_classes=DATASET_TO_CLASSES[args["dataset"]],
    )
    print("TensorFlow model instantiated, populating pretrained weights...")

    # Fetch the pretrained parameters.
    param_list = list(mobilevit_model_pt.parameters())
    model_states = mobilevit_model_pt.state_dict()
    state_list = list(model_states.keys())

    # Stem block
    stem_layer_conv = mobilevit_model_tf.get_layer("stem_block_conv_1")

    if isinstance(stem_layer_conv, layers.Conv2D):
        print("Stem Conv 1")
        stem_layer_conv.kernel.assign(
            tf.Variable(param_list[0].numpy().transpose(2, 3, 1, 0))
        )
        stem_layer_conv.bias.assign(tf.Variable(param_list[1].numpy()))

    stem_layer_bn = mobilevit_model_tf.get_layer("stem_block_bn_1")
    if isinstance(stem_layer_bn, layers.BatchNormalization):
        print("Stem Bn 2")
        stem_layer_bn.gamma.assign(
            tf.Variable(
                model_states["mobilevit.conv_stem.normalization.weight"].numpy()
            )
        )
        stem_layer_bn.beta.assign(
            tf.Variable(model_states["mobilevit.conv_stem.normalization.bias"].numpy())
        )

    # inverted residual block 1 - (expand_1x1)
    inverted_residual_1_conv_1_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_1_conv_1"
    )
    inverted_residual_1_conv_1_pt = model_states[
        "mobilevit.encoder.layer.0.layer.0.expand_1x1.convolution.weight"
    ]
    if isinstance(inverted_residual_1_conv_1_tf, layers.Conv2D):
        print("inverted_residual_1_conv_1_tf 3")
        inverted_residual_1_conv_1_tf.kernel.assign(
            tf.Variable(inverted_residual_1_conv_1_pt.numpy().transpose(2, 3, 1, 0))
        )

    inverted_residual_1_bn_1_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_1_bn_1"
    )
    if isinstance(inverted_residual_1_bn_1_tf, layers.BatchNormalization):
        print("inverted_residual_1_bn_1_tf 4")
        inverted_residual_1_bn_1_tf.gamma.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.0.layer.0.expand_1x1.normalization.weight"
                ].numpy()
            )
        )
        inverted_residual_1_bn_1_tf.beta.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.0.layer.0.expand_1x1.normalization.bias"
                ].numpy()
            )
        )

    # inverted residual block 1 - (conv_3x3)
    inverted_residual_1_conv_2_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_1_conv_2"
    )
    inverted_residual_1_conv_2_pt = model_states[
        "mobilevit.encoder.layer.0.layer.0.conv_3x3.convolution.weight"
    ]
    if isinstance(inverted_residual_1_conv_2_tf, layers.Conv2D):
        print("inverted_residual_1_conv_2_tf 5")
        inverted_residual_1_conv_2_tf.kernel.assign(
            tf.Variable(inverted_residual_1_conv_2_pt.numpy().transpose(2, 3, 1, 0))
        )

    inverted_residual_1_bn_2_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_1_bn_2"
    )
    if isinstance(inverted_residual_1_bn_2_tf, layers.BatchNormalization):
        print("inverted_residual_1_bn_2_tf 6")
        inverted_residual_1_bn_2_tf.gamma.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.0.layer.0.conv_3x3.normalization.weight"
                ].numpy()
            )
        )
        inverted_residual_1_bn_2_tf.beta.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.0.layer.0.conv_3x3.normalization.bias"
                ].numpy()
            )
        )

    # inverted residual block - 1 (reduce_1x1)
    inverted_residual_1_conv_3_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_1_conv_3"
    )
    inverted_residual_1_conv_3_pt = model_states[
        "mobilevit.encoder.layer.0.layer.0.reduce_1x1.convolution.weight"
    ]
    if isinstance(inverted_residual_1_conv_3_tf, layers.Conv2D):
        print("inverted_residual_1_conv_3_tf 7")
        inverted_residual_1_conv_3_tf.kernel.assign(
            tf.Variable(inverted_residual_1_conv_3_pt.numpy().transpose(2, 3, 1, 0))
        )

    inverted_residual_1_bn_3_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_1_bn_3"
    )
    if isinstance(inverted_residual_1_bn_3_tf, layers.BatchNormalization):
        print("inverted_residual_1_bn_3_tf 8")
        inverted_residual_1_bn_3_tf.gamma.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.0.layer.0.reduce_1x1.normalization.weight"
                ].numpy()
            )
        )
        inverted_residual_1_bn_3_tf.beta.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.0.layer.0.reduce_1x1.normalization.bias"
                ].numpy()
            )
        )

    # inverted residual block - 2 - (expand_1x1)
    inverted_residual_2_conv_1_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_2_conv_1"
    )
    inverted_residual_2_conv_1_pt = model_states[
        "mobilevit.encoder.layer.1.layer.0.expand_1x1.convolution.weight"
    ]
    if isinstance(inverted_residual_2_conv_1_tf, layers.Conv2D):
        print("inverted_residual_2_conv_1_tf 9")
        inverted_residual_2_conv_1_tf.kernel.assign(
            tf.Variable(inverted_residual_2_conv_1_pt.numpy().transpose(2, 3, 1, 0))
        )

    inverted_residual_2_bn_1_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_2_bn_1"
    )
    if isinstance(inverted_residual_2_bn_1_tf, layers.BatchNormalization):
        print("inverted_residual_2_bn_1_tf 10")
        inverted_residual_2_bn_1_tf.gamma.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.1.layer.0.expand_1x1.normalization.weight"
                ].numpy()
            )
        )
        inverted_residual_2_bn_1_tf.beta.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.1.layer.0.expand_1x1.normalization.bias"
                ].numpy()
            )
        )

    # inverted residual block - 2 - (conv_3x3)
    inverted_residual_2_conv_2_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_2_conv_2"
    )
    inverted_residual_2_conv_2_pt = model_states[
        "mobilevit.encoder.layer.1.layer.0.conv_3x3.convolution.weight"
    ]
    if isinstance(inverted_residual_2_conv_2_tf, layers.Conv2D):
        print("inverted_residual_2_conv_2_tf 11")
        inverted_residual_2_conv_2_tf.kernel.assign(
            tf.Variable(inverted_residual_2_conv_2_pt.numpy().transpose(2, 3, 1, 0))
        )

    inverted_residual_2_bn_2_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_2_bn_2"
    )
    if isinstance(inverted_residual_2_bn_2_tf, layers.BatchNormalization):
        print("inverted_residual_2_bn_2_tf 12")
        inverted_residual_2_bn_2_tf.gamma.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.1.layer.0.conv_3x3.normalization.weight"
                ].numpy()
            )
        )
        inverted_residual_2_bn_2_tf.beta.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.1.layer.0.conv_3x3.normalization.bias"
                ].numpy()
            )
        )

    # inverted residual block - 2 - (reduce_1x1)
    inverted_residual_2_conv_3_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_2_conv_3"
    )
    inverted_residual_2_conv_3_pt = model_states[
        "mobilevit.encoder.layer.1.layer.0.reduce_1x1.convolution.weight"
    ]
    if isinstance(inverted_residual_2_conv_3_tf, layers.Conv2D):
        print("inverted_residual_2_conv_3_tf 13")
        inverted_residual_2_conv_3_tf.kernel.assign(
            tf.Variable(inverted_residual_2_conv_3_pt.numpy().transpose(2, 3, 1, 0))
        )

    inverted_residual_2_bn_3_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_2_bn_3"
    )
    if isinstance(inverted_residual_2_bn_3_tf, layers.BatchNormalization):
        print("inverted_residual_2_bn_3_tf 14")
        inverted_residual_2_bn_3_tf.gamma.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.1.layer.0.reduce_1x1.normalization.weight"
                ].numpy()
            )
        )
        inverted_residual_2_bn_3_tf.beta.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.1.layer.0.reduce_1x1.normalization.bias"
                ].numpy()
            )
        )

    # inverted residual block - 3 - (expand_1x1)
    inverted_residual_3_conv_1_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_3_conv_1"
    )
    inverted_residual_3_conv_1_pt = model_states[
        "mobilevit.encoder.layer.1.layer.1.expand_1x1.convolution.weight"
    ]
    if isinstance(inverted_residual_3_conv_1_tf, layers.Conv2D):
        print("inverted_residual_3_conv_1_tf 15")
        inverted_residual_3_conv_1_tf.kernel.assign(
            tf.Variable(inverted_residual_3_conv_1_pt.numpy().transpose(2, 3, 1, 0))
        )

    inverted_residual_3_bn_1_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_3_bn_1"
    )
    if isinstance(inverted_residual_3_bn_1_tf, layers.BatchNormalization):
        print("inverted_residual_3_bn_1_tf 16")
        inverted_residual_3_bn_1_tf.gamma.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.1.layer.1.expand_1x1.normalization.weight"
                ].numpy()
            )
        )
        inverted_residual_3_bn_1_tf.beta.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.1.layer.1.expand_1x1.normalization.bias"
                ].numpy()
            )
        )

    # inverted residual block - 3 - (conv_3x3)
    inverted_residual_3_conv_2_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_3_conv_2"
    )
    inverted_residual_3_conv_2_pt = model_states[
        "mobilevit.encoder.layer.1.layer.1.conv_3x3.convolution.weight"
    ]
    if isinstance(inverted_residual_3_conv_2_tf, layers.Conv2D):
        print("inverted_residual_3_conv_2_tf 17")
        inverted_residual_3_conv_2_tf.kernel.assign(
            tf.Variable(inverted_residual_3_conv_2_pt.numpy().transpose(2, 3, 1, 0))
        )

    inverted_residual_3_bn_2_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_3_bn_2"
    )
    if isinstance(inverted_residual_3_bn_2_tf, layers.BatchNormalization):
        print("inverted_residual_3_bn_2_tf 18")
        inverted_residual_3_bn_2_tf.gamma.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.1.layer.1.conv_3x3.normalization.weight"
                ].numpy()
            )
        )
        inverted_residual_3_bn_2_tf.beta.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.1.layer.1.conv_3x3.normalization.bias"
                ].numpy()
            )
        )

    # inverted residual block - 3 - (reduce_1x1)
    inverted_residual_3_conv_3_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_3_conv_3"
    )
    inverted_residual_3_conv_3_pt = model_states[
        "mobilevit.encoder.layer.1.layer.1.reduce_1x1.convolution.weight"
    ]
    if isinstance(inverted_residual_3_conv_3_tf, layers.Conv2D):
        print("inverted_residual_3_conv_3_tf 19")
        inverted_residual_3_conv_3_tf.kernel.assign(
            tf.Variable(inverted_residual_3_conv_3_pt.numpy().transpose(2, 3, 1, 0))
        )

    inverted_residual_3_bn_3_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_3_bn_3"
    )
    if isinstance(inverted_residual_3_bn_3_tf, layers.BatchNormalization):
        print("inverted_residual_3_bn_3_tf 20")
        inverted_residual_3_bn_3_tf.gamma.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.1.layer.1.reduce_1x1.normalization.weight"
                ].numpy()
            )
        )
        inverted_residual_3_bn_3_tf.beta.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.1.layer.1.reduce_1x1.normalization.bias"
                ].numpy()
            )
        )

    # inverted residual block - 4 - (expand_1x1)
    inverted_residual_4_conv_1_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_4_conv_1"
    )
    inverted_residual_4_conv_1_pt = model_states[
        "mobilevit.encoder.layer.1.layer.2.expand_1x1.convolution.weight"
    ]
    if isinstance(inverted_residual_4_conv_1_tf, layers.Conv2D):
        print("inverted_residual_4_conv_1_tf 21")
        inverted_residual_4_conv_1_tf.kernel.assign(
            tf.Variable(inverted_residual_4_conv_1_pt.numpy().transpose(2, 3, 1, 0))
        )

    inverted_residual_4_bn_1_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_4_bn_1"
    )
    if isinstance(inverted_residual_4_bn_1_tf, layers.BatchNormalization):
        print("inverted_residual_4_bn_1_tf 22")
        inverted_residual_4_bn_1_tf.gamma.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.1.layer.2.expand_1x1.normalization.weight"
                ].numpy()
            )
        )
        inverted_residual_4_bn_1_tf.beta.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.1.layer.2.expand_1x1.normalization.bias"
                ].numpy()
            )
        )

    # inverted residual block - 4 - (conv_3x3)
    inverted_residual_4_conv_2_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_4_conv_2"
    )
    inverted_residual_4_conv_2_pt = model_states[
        "mobilevit.encoder.layer.1.layer.2.conv_3x3.convolution.weight"
    ]
    if isinstance(inverted_residual_4_conv_2_tf, layers.Conv2D):
        print("inverted_residual_4_conv_2_tf 23")
        inverted_residual_4_conv_2_tf.kernel.assign(
            tf.Variable(inverted_residual_4_conv_2_pt.numpy().transpose(2, 3, 1, 0))
        )

    inverted_residual_4_bn_2_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_4_bn_2"
    )
    if isinstance(inverted_residual_4_bn_2_tf, layers.BatchNormalization):
        print("inverted_residual_4_bn_2_tf 24")
        inverted_residual_4_bn_2_tf.gamma.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.1.layer.2.conv_3x3.normalization.weight"
                ].numpy()
            )
        )
        inverted_residual_4_bn_2_tf.beta.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.1.layer.2.conv_3x3.normalization.bias"
                ].numpy()
            )
        )

    # inverted residual block - 4 - (reduce_1x1)
    inverted_residual_4_conv_3_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_4_conv_3"
    )
    inverted_residual_4_conv_3_pt = model_states[
        "mobilevit.encoder.layer.1.layer.2.reduce_1x1.convolution.weight"
    ]
    if isinstance(inverted_residual_4_conv_3_tf, layers.Conv2D):
        print("inverted_residual_4_conv_3_tf 25")
        inverted_residual_4_conv_3_tf.kernel.assign(
            tf.Variable(inverted_residual_4_conv_3_pt.numpy().transpose(2, 3, 1, 0))
        )

    inverted_residual_4_bn_3_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_4_bn_3"
    )
    if isinstance(inverted_residual_4_bn_3_tf, layers.BatchNormalization):
        print("inverted_residual_4_bn_3_tf 26")
        inverted_residual_4_bn_3_tf.gamma.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.1.layer.2.reduce_1x1.normalization.weight"
                ].numpy()
            )
        )
        inverted_residual_4_bn_3_tf.beta.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.1.layer.2.reduce_1x1.normalization.bias"
                ].numpy()
            )
        )

    # inverted residual block - 5 - (expand_1x1)
    inverted_residual_5_conv_1_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_5_conv_1"
    )
    inverted_residual_5_conv_1_pt = model_states[
        "mobilevit.encoder.layer.2.downsampling_layer.expand_1x1.convolution.weight"
    ]
    if isinstance(inverted_residual_5_conv_1_tf, layers.Conv2D):
        print("inverted_residual_5_conv_1_tf 27")
        inverted_residual_5_conv_1_tf.kernel.assign(
            tf.Variable(inverted_residual_5_conv_1_pt.numpy().transpose(2, 3, 1, 0))
        )

    inverted_residual_5_bn_1_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_5_bn_1"
    )
    if isinstance(inverted_residual_5_bn_1_tf, layers.BatchNormalization):
        print("inverted_residual_5_bn_1_tf 28")
        inverted_residual_5_bn_1_tf.gamma.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.2.downsampling_layer.expand_1x1.normalization.weight"
                ].numpy()
            )
        )
        inverted_residual_5_bn_1_tf.beta.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.2.downsampling_layer.expand_1x1.normalization.bias"
                ].numpy()
            )
        )

    # inverted residual block - 5 - (conv_3x3)
    inverted_residual_5_conv_2_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_5_conv_2"
    )
    inverted_residual_5_conv_2_pt = model_states[
        "mobilevit.encoder.layer.2.downsampling_layer.conv_3x3.convolution.weight"
    ]
    if isinstance(inverted_residual_5_conv_2_tf, layers.Conv2D):
        print("inverted_residual_5_conv_2_tf 29")
        inverted_residual_5_conv_2_tf.kernel.assign(
            tf.Variable(inverted_residual_5_conv_2_pt.numpy().transpose(2, 3, 1, 0))
        )

    inverted_residual_5_bn_2_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_5_bn_2"
    )
    if isinstance(inverted_residual_5_bn_2_tf, layers.BatchNormalization):
        print("inverted_residual_5_bn_2_tf 30")
        inverted_residual_5_bn_2_tf.gamma.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.2.downsampling_layer.conv_3x3.normalization.weight"
                ].numpy()
            )
        )
        inverted_residual_5_bn_2_tf.beta.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.2.downsampling_layer.conv_3x3.normalization.bias"
                ].numpy()
            )
        )

    # inverted residual block - 5 - (reduce_1x1)
    inverted_residual_5_conv_3_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_5_conv_3"
    )
    inverted_residual_5_conv_3_pt = model_states[
        "mobilevit.encoder.layer.2.downsampling_layer.reduce_1x1.convolution.weight"
    ]
    if isinstance(inverted_residual_5_conv_3_tf, layers.Conv2D):
        print("inverted_residual_5_conv_3_tf 31")
        inverted_residual_5_conv_3_tf.kernel.assign(
            tf.Variable(inverted_residual_5_conv_3_pt.numpy().transpose(2, 3, 1, 0))
        )

    inverted_residual_5_bn_3_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_5_bn_3"
    )
    if isinstance(inverted_residual_5_bn_3_tf, layers.BatchNormalization):
        print("inverted_residual_5_bn_3_tf 32")
        inverted_residual_5_bn_3_tf.gamma.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.2.downsampling_layer.reduce_1x1.normalization.weight"
                ].numpy()
            )
        )
        inverted_residual_5_bn_3_tf.beta.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.2.downsampling_layer.reduce_1x1.normalization.bias"
                ].numpy()
            )
        )

    mobilevit_1_conv_1_tf = mobilevit_model_tf.get_layer("1conv_1")
    mobilevit_1_conv_1_pt = model_states[
        "mobilevit.encoder.layer.2.conv_kxk.convolution.weight"
    ]
    if isinstance(mobilevit_1_conv_1_tf, layers.Conv2D):
        print("mobilevit_1_conv_1_tf 33")
        mobilevit_1_conv_1_tf.kernel.assign(
            tf.Variable(mobilevit_1_conv_1_pt.numpy().transpose(2, 3, 1, 0))
        )

    mobilevit_1_bn_1_tf = mobilevit_model_tf.get_layer("batch_normalization")
    if isinstance(mobilevit_1_bn_1_tf, layers.BatchNormalization):
        print("mobilevit_1_bn_1_tf 34")
        mobilevit_1_bn_1_tf.gamma.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.2.conv_kxk.normalization.weight"
                ].numpy()
            )
        )
        mobilevit_1_bn_1_tf.beta.assign(
            tf.Variable(
                model_states[
                    "mobilevit.encoder.layer.2.conv_kxk.normalization.bias"
                ].numpy()
            )
        )

    mobilevit_1_conv_2_tf = mobilevit_model_tf.get_layer("2conv_1")
    mobilevit_2_conv_1_pt = model_states[
        "mobilevit.encoder.layer.2.conv_1x1.convolution.weight"
    ]
    if isinstance(mobilevit_1_conv_2_tf, layers.Conv2D):
        print("mobilevit_1_conv_1_tf 35")
        mobilevit_1_conv_2_tf.kernel.assign(
            tf.Variable(mobilevit_2_conv_1_pt.numpy().transpose(2, 3, 1, 0))
        )

    inverted_residual_6_conv_1_tf = mobilevit_model_tf.get_layer(
        "inverted_residual_block_6_conv_1"
    )
    inverted_residual_6_conv_1_pt = model_states[
        "mobilevit.encoder.layer.3.downsampling_layer.expand_1x1.convolution.weight"
    ]
    if isinstance(inverted_residual_6_conv_1_tf, layers.Conv2D):
        print("inverted_residual_6_conv_1_tf 36")
        inverted_residual_6_conv_1_tf.kernel.assign(
            tf.Variable(inverted_residual_6_conv_1_pt.numpy().transpose(2, 3, 1, 0))
        )

    print("Weight population successful, serializing TensorFlow model...")
    # model_name = f'{args["model_name"]}_{args["image_resolution"]}'
    # save_path = os.path.join(TF_MODEL_ROOT, model_name)
    # mobilevit_model_tf.save(save_path)
    # print(f"TensorFlow model serialized to: {save_path}...")


if __name__ == "__main__":
    args = parse_args()
    main(args)
