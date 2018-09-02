# !/usr/local/bin/python3
# _*_ coding:utf-8 _*_

import tensorflow as tf

x = tf.Variable(5, name='x')
y = tf.Variable(2, name='y')
f = x*x*y + y + 10

init = tf.global_variables_initializer()

with tf.Session() as sess:
    init.run()
    result = f.eval()
    print(result)
    sess.close()