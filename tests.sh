python -m scripts.retrain \
--bottleneck_dir=tf_malalties/bottlenecks \
--how_many_training_steps=4000 \
--model_dir=tf_malalties/models \
--summaries_dir=tf_malalties/training_summaries/mobilenet_1.0_224 \
--output_graph=tf_malalties/retrained_graph.pb \
--output_labels=tf_malalties/retrained_labels.txt \
--architecture=mobilenet_1.0_224 \
--image_dir=tf_malalties/malalties_first
