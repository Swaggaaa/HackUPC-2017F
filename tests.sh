python -m scripts.retrain \
--bottleneck_dir=tf_malalties7/bottlenecks \
--how_many_training_steps=1000 \
--model_dir=tf_malalties7/models \
--summaries_dir=tf_malalties7/training_summaries/mobilenet_1.0_224 \
--output_graph=tf_malalties7/retrained_graph.pb \
--output_labels=tf_malalties7/retrained_labels.txt \
--architecture=mobilenet_1.0_224 \
--image_dir=malalties-03
