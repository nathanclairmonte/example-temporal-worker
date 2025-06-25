# Example Temporal Worker

Example repo to showcase how to create Temporal Activities, Workflows and workers for use with [`temporal-worker-k8s` charm](https://github.com/canonical/temporal-worker-k8s-operator). This charm allows us to deploy Temporal workers in Juju, registered with the Temporal Activities and Workflows we need them to run. In order to use it, we just need to deploy a new instance of the charm and pass it a Rock image as a resource containing our packaged Activities, Workflows and worker (detailed in the [README of the charm repo](https://github.com/canonical/temporal-worker-k8s-operator/blob/main/README.md#deploying)).

> **Note:** The charm also appears to support using Python wheel files, detailed in the [Charmhub docs](https://charmhub.io/temporal-k8s/docs/t-deploy-worker). However, we only use the Rock image approach in this repo.

This example uses the [sample](https://github.com/canonical/temporal-worker-k8s-operator/tree/main/resource_sample_py) from the charm repo as a reference to create this Rock image, but uses [uv](https://docs.astral.sh/uv/) and [Taskfile](https://taskfile.dev/) instead of Poetry/Makefile.
