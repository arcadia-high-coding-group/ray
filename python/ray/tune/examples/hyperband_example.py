#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import os
import random

import numpy as np

import ray
from ray.tune import Trainable, TrainingResult, register_trainable, \
    run_experiments
from ray.tune.hyperband import HyperBandScheduler


class MyTrainableClass(Trainable):
    """Example agent whose learning curve is a random sigmoid.

    The dummy hyperparameters "width" and "height" determine the slope and
    maximum reward value reached.
    """

    def _setup(self):
        self.timestep = 0

    def _train(self):
        self.timestep += 1
        v = np.tanh(float(self.timestep) / self.config["width"])
        v *= self.config["height"]

        # Here we use `episode_reward_mean`, but you can also report other
        # objectives such as loss or accuracy (see tune/result.py).
        return TrainingResult(episode_reward_mean=v, timesteps_this_iter=1)

    def _save(self, checkpoint_dir):
        path = os.path.join(checkpoint_dir, "checkpoint")
        with open(path, "w") as f:
            f.write(json.dumps({"timestep": self.timestep}))
        return path

    def _restore(self, checkpoint_path):
        with open(checkpoint_path) as f:
            self.timestep = json.loads(f.read())["timestep"]


register_trainable("my_class", MyTrainableClass)

if __name__ == "__main__":
    ray.init()

    # Hyperband early stopping, configured with `episode_reward_mean` as the
    # objective and `timesteps_total` as the time unit.
    hyperband = HyperBandScheduler(
        time_attr="timesteps_total", reward_attr="episode_reward_mean",
        max_t=100)

    run_experiments({
        "hyperband_test": {
            "run": "my_class",
            "repeat": 100,
            "resources": {"cpu": 1, "gpu": 0},
            "config": {
                "width": lambda spec: 10 + int(90 * random.random()),
                "height": lambda spec: int(100 * random.random()),
            },
        }
    }, scheduler=hyperband)
