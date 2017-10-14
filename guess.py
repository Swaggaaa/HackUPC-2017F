import tensorflow as tf
import sys
import numpy as np
import plotly.plotly as ply
import plotly.graph_objs as go
import datetime


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
    ply.sign_in('ferranconde', 'XL3PlhOhEHG8PzgxDNXC')

    # load graph (previously retrained) and read image data
    # paths are hardcoded cuz ye
    graph = load_graph("test_merged/retrained_graph_mobilenet.pb")
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
    labels = load_labels("test_merged/retrained_labels_mobilenet.txt")
    def_results = []
    def_results.append(labels[top_k[0]])
    if results[top_k[0]] < 0.7:
        def_results.append(labels[top_k[1]])

    # plotting pie chart
    plot_labels = [labels[i] for i in top_k]
    if 'good eye' in plot_labels:
        plot_labels[plot_labels.index('good eye')] = 'Healthy eye'
    if 'perfectsmile' in plot_labels:
        plot_labels[plot_labels.index('perfectsmile')] = 'Healthy teeth'
    plot_labels = [i.capitalize() for i in plot_labels]
    trace = go.Pie(labels=plot_labels,
                   values=[results[i]*100.0 for i in top_k],
                   textinfo="label+percent",
                   textfont=dict(size=42),
                   marker=dict(colors=['#0080ff', '#3399ff', '#66b3ff', '#99ccff', '#cce6ff']))
    layout = go.Layout(title='Prediction results', titlefont=dict(size=55),
                       width=1560, height=1660,
                       legend=dict(font=dict(size=35)))
    fig = go.Figure(data=[trace], layout=layout)
    pie_filename = "pred_results_" + str(datetime.datetime.now()).replace(' ', '_')
    ply.image.save_as(fig, filename=pie_filename+'.png')

    return def_results, pie_filename+'.png'
