# Example Temporal Worker

Example repo to showcase how to create Temporal Activities, Workflows and workers for use with [`temporal-worker-k8s` charm](https://github.com/canonical/temporal-worker-k8s-operator). This charm allows us to deploy Temporal workers in Juju, registered with the Temporal Activities and Workflows we need them to run. In order to use it, we just need to deploy a new instance of the charm and pass it a Rock image as a resource containing our packaged Activities, Workflows and worker (detailed in the [README of the charm repo](https://github.com/canonical/temporal-worker-k8s-operator/blob/main/README.md#deploying)).

> **Note:** The charm also appears to support using Python wheel files, detailed in the [Charmhub docs](https://charmhub.io/temporal-k8s/docs/t-deploy-worker). However, we only use the Rock image approach in this repo.

This example uses the [sample](https://github.com/canonical/temporal-worker-k8s-operator/tree/main/resource_sample_py) from the charm repo as a reference to create this Rock image, but uses [uv](https://docs.astral.sh/uv/) and [Taskfile](https://taskfile.dev/) instead of Poetry/Makefile.

## 0. Tools

You'll need the following tools:
- [docker](https://www.docker.com/)
- [rockcraft](https://snapcraft.io/rockcraft)
- [temporal CLI](https://docs.temporal.io/cli)
    ```bash
    # N.B. For some reason their docs don't mention this install script anymore, but it still works for me at time of writing
    curl -sSf https://temporal.download/cli.sh | sh
    ```
- [uv](https://docs.astral.sh/uv/)
- [Taskfile](https://taskfile.dev/)
- [Juju](https://snapcraft.io/juju)
- [Microk8s](https://snapcraft.io/microk8s)

## 1. Run the Rock locally

This section outlines how to pack and run the rock locally with Docker. It is a good idea to do this before deploying the charm, just to ensure everything works in your rock.

1. First pack the rock.
    ```bash
    rockcraft pack -v
    ```

2. Load the rock into local docker registry (`ROCK_NAME` is the name of the .rock file produced by the first step, and `IMAGE_NAME` is your choice).
    ```bash
    rockcraft.skopeo --insecure-policy copy oci-archive:$ROCK_NAME docker-daemon:$IMAGE_NAME
    ```

3. Run the rock with docker. The `CONTAINER_NAME` here is also your choice.
    ```bash
    # N.B. we set --network to host here because my local Temporal server will be running on my host and not in the container. if your setup is different, feel free to change or remove this
    docker run --rm -d --name $CONTAINER_NAME --network host $IMAGE_NAME
    ```

4. Once the rock container is running, exec into it.
    ```bash
    docker exec -it $CONTAINER_NAME bash
    ```

5. Once inside the rock container, you should be able to run Pebble commands. Start the `temporal-worker` service with Pebble and follow the logs.
    ```bash
    # to view the temporal-worker service you defined in rockcraft.yaml
    pebble services

    # to start it
    pebble start temporal-worker

    # to follow logs
    pebble logs temporal-worker -f
    ```

6. That's it for this side really. At this point your worker should be running and will already be polling the Temporal server you defined in `TEMPORAL_HOST` to receive tasks to run. You can move to the next section to use a local Temporal server and scripts defined in this repo to run the example Workflow. However, the running worker should pick up tasks regardless of where your `TEMPORAL_HOST` server lives or how you choose to start your Workflow.

## 2. Start the example Workflow with a local Temporal server

This section outlines how to use your worker rock running in Docker to execute a Workflow. It uses a local Temporal server and a custom script to start the example Workflow.

1. From a new local terminal (i.e. not inside the running rock container), start a local Temporal dev server and view the Temporal Web UI at http://localhost:8080.
    ```bash
    # N.B. --ui-port here is optional, I just like using 8080. Default is 8233.
    temporal server start-dev --ui-port 8080
    ```

2. In another new local terminal, trigger the example workflow. You should be able to see the worker picking up and running this tasks in the pebble logs you followed in step 5 of the previous section.
    ```bash
    task start-workflow
    ```

## 3. Clean up local docker run

Once you are sure the rock works as expected, you can clean up the docker container and image from the first section. This section outlines how to do so.

1. Stop the running container
    ```bash
    docker stop $CONTAINER_NAME
    ```
2. Remove the image
    ```bash
    docker rmi $IMAGE_NAME
    ```
3. **(Optional)** Use the Taskfile command from this repo to perform steps 1 and 2 automatically.
    ```bash
    task cleanup-docker
    ```

## 4. Deploy the `temporal-worker-k8s` charm

This section outlines how to deploy the `temporal-worker-k8s` charm and pass our rock as resource. This section assumes you already have Juju set up with microk8s on your machine, as well as a charmed Temporal cluster already set up in a separate Juju model. Links to help you set up these two prerequisites below:
- [Set up local Juju environment with microk8s](https://charmhub.io/temporal-k8s/docs/t-setup-environment) (**N.B.** [Here is an additional blog post from Goulin about setting up Juju with microk8s](https://discourse.canonical.com/t/setting-up-juju-and-cos-lite-on-microk8s/4860). The MetalLB and COS-Lite steps are not necessary for this.)
- [Deploy the Temporal server charm](https://charmhub.io/temporal-k8s/docs/t-deploy-server)
- [Deploy a Postgres db for Temporal](https://charmhub.io/temporal-k8s/docs/t-deploy-db)
- [Deploy the Temporal admin charm](https://charmhub.io/temporal-k8s/docs/t-deploy-admin)
- [Deploy the Temporal UI charm](https://charmhub.io/temporal-k8s/docs/t-deploy-ui)
- [Deploy Ingress for the server and UI charms](https://charmhub.io/temporal-k8s/docs/t-deploy-ingress)

> N.B. The Charmhub docs for deploying ingress appear to reference an older version of the `nginx-ingress-integrator` charm. New versions cannot be related with multiple applications. Therefore, you will have to deploy two separate instances of the `nginx-ingress-integrator` charm and relate them to the server and UI charms respectively.

1. Upload the previously packed rock to the local microk8s registry (as before, `ROCK_NAME` is the name of your .rock file, and `IMAGE_NAME` is your choice).
    ```bash
    rockcraft.skopeo --insecure-policy copy --dest-tls-verify=false \
        oci-archive:$ROCK_NAME \
        docker://localhost:32000/$IMAGE_NAME
    ```

2. Add a new Juju model for the worker
    ```bash
    juju add-model worker-model
    ```

3. Deploy the `temporal-worker-k8s` charm and pass it your rock as resource
    ```bash
    juju deploy temporal-worker-k8s --resource temporal-worker-image=localhost:32000/$IMAGE_NAME
    ```

4. Configure the charm (here the `TEMPORAL_HOST` value refers to the hostname of the Temporal server charm, and the `QUEUE_NAME` is the one defined in your Workflow code)
    ```bash
    juju config temporal-worker-k8s \
        host="$TEMPORAL_HOST" \
        queue="$QUEUE_NAME" \
        namespace="default"
    ```

5. View the logs for the charmed worker, should look similar to the logs when you followed them in pebble earlier
    ```bash
    microk8s kubectl -n worker-model logs temporal-worker-k8s-0 -c temporal-worker
    ```

6. Start a Workflow using the Temporal admin charm
    ```bash
    # first switch back to your Temporal cluster Juju model
    juju switch temporal-model

    # then start a Workflow
    juju run temporal-admin-k8s/0 tctl args='workflow start --taskqueue example-workflow-queue --workflow_type FakeReplicateJobPostsWorkflow --execution_timeout 30 --input {"source_post_id":11111,"regions":["americas"],"job_id":22222,"user_email":"nathan.clairmonte@canonical.com"}'
    ```

7. Aaand that's it! Similar to before, you should see in the worker logs that it picks up the newly started task and executes it. From here, you would either start Workflows manually from an application (using the Temporal Client SDK), or set up a Temporal Schedule to run the Workflows on a pre-defined schedule.
