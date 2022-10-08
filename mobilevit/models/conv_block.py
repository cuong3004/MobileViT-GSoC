from typing import Tuple

import tensorflow as tf
from keras import backend, layers
from keras.applications import imagenet_utils
from tensorflow import keras


def conv_block(
    input_layer: layers.Input,
    num_filters: int = 16,
    kernel_size: Tuple[int, int] = (3, 3),
    strides: int = 2,
    name=None,
):
    """
    3x3 Convolutional Stem Stage.

    Args:
        input_layer: input tensor
        num_filters (int): number of filters in the convolutional layer
        kernel_size (Tuple[int, int]): kernel size of the convolution layer
        strides (int): stride of the convolutional layer
        name (str): name of the layer

    Returns:
        output tensor of the convolutional block
    """

    if name is None:
        name = str(backend.get_uid("conv_block"))

    conv_1 = layers.Conv2D(
        filters=num_filters,
        kernel_size=kernel_size,
        strides=strides,
        padding="same",
        activation=tf.nn.swish,
        name=name + "conv_1",
    )(input_layer)
    return conv_1


def inverted_residual_block(
    input_layer: layers.Input,
    expanded_channels: int,
    output_channels: int,
    strides: int = 1,
    name: str = "",
):
    """
    Inverted Residual Block.

    Args:
        input_layer: input tensor
        expanded_channels (int): number of filters in the expanded convolutional layer
        output_channels (int): number of filters in the output convolutional layer
        strides (int): stride of the convolutional layer
        name (str): name of the layer
    Returns:
        output tensor of the inverted residual block
    """
    conv_1 = layers.Conv2D(
        filters=expanded_channels,
        kernel_size=(1, 1),
        strides=1,
        padding="same",
        use_bias=False,
        name=name + "conv_1",
    )(input_layer)
    bn_1 = layers.BatchNormalization(
        name=name + "bn_1",
    )(conv_1)
    act_1 = tf.nn.swish(bn_1)

    if strides == 2:
        act_1 = layers.ZeroPadding2D(
            padding=imagenet_utils.correct_pad(act_1, 3), name=name + "pad_1"
        )(act_1)

    conv_2 = layers.Conv2D(
        filters=expanded_channels,
        kernel_size=(3, 3),
        strides=strides,
        padding="same" if strides == 1 else "valid",
        groups=expanded_channels,
        use_bias=False,
        name=name + "conv_2",
    )(act_1)
    bn_2 = layers.BatchNormalization(
        name=name + "bn_2",
    )(conv_2)
    act_2 = tf.nn.swish(bn_2)

    conv_3 = layers.Conv2D(
        filters=output_channels,
        kernel_size=(1, 1),
        padding="same",
        use_bias=False,
        name=name + "conv_3",
    )(act_2)
    bn_3 = layers.BatchNormalization(
        name=name + "bn_3",
    )(conv_3)

    if tf.math.equal(input_layer.shape[-1], output_channels) and strides == 1:
        return layers.Add(
            name=name + "add",
        )([bn_3, input_layer])
    return bn_3
