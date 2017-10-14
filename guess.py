import tensorflow as tf
import sys
import numpy as np


# usage: python guess.py <path_to_image>

# load graph
def load_graph(model_file):
    graph = tf.Graph()
    graph_def = tf.GraphDef()

    with open(model_file, "rb") as f:
        graph_def.ParseFromString(f.read())
    with graph.as_default():
        tf.import_graph_def(graph_def)

    return graph


# load labels
def load_labels(label_file):
    return [l.rstrip() for l in tf.gfile.GFile(label_file).readlines()]


# handy function with defaults and handlers for different formats
def read_tensor_from_image_file(file_name, input_height=224, input_width=224, input_mean=128, input_std=128):

    input_name = "file_reader"
    output_name = "normalized"
    file_reader = tf.read_file(file_name, input_name)
    if file_name.endswith(".png"):
        image_reader = tf.image.decode_png(file_reader, channels = 3, name='png_reader')
    elif file_name.endswith(".gif"):
        image_reader = tf.squeeze(tf.image.decode_gif(file_reader, name='gif_reader'))
    elif file_name.endswith(".bmp"):
        image_reader = tf.image.decode_bmp(file_reader, name='bmp_reader')
    else:
        image_reader = tf.image.decode_jpeg(file_reader, channels = 3, name='jpeg_reader')

    float_caster = tf.cast(image_reader, tf.float32)
    dims_expander = tf.expand_dims(float_caster, 0);
    resized = tf.image.resize_bilinear(dims_expander, [input_height, input_width])
    normalized = tf.divide(tf.subtract(resized, [input_mean]), [input_std])
    sess = tf.Session()
    result = sess.run(normalized)

    return result


def diagnostic(filename):
    # load graph (previously retrained) and read image data
    # paths are hardcoded cuz ye
    graph = load_graph("tf_malalties/retrained_graph.pb")
    t = read_tensor_from_image_file(filename)

    # run the simulation and get the results
    input_name = "import/input"
    output_name = "import/final_result"
    input_operation = graph.get_operation_by_name(input_name);
    output_operation = graph.get_operation_by_name(output_name);

    with tf.Session(graph=graph) as sess:
        results = sess.run(output_operation.outputs[0], {input_operation.outputs[0]: t})
    results = np.squeeze(results)

    # sorted by most reasonable answer first
    top_k = results.argsort()[-5:][::-1]
    labels = load_labels("tf_malalties/retrained_labels.txt")
    def_results = [labels[0]]
    if results[0] < 0.7 and len(labels) > 1:
        def_results.append(labels[1])
