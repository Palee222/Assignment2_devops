## Dependency installations

rest of the explanations for assignment 2 is in Dev2

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r services/service1/requirements.txt \ -r services/service2/requirements.txt

    cd ui
    npm run lint

Copilot is only there as a contributor because I asked it to push some modified files to my github.

Very important note:

> I tried all five allowed regions. Poland Central and Germany West Central refuse to create SQL servers. In Belgium Central, Denmark East and Spain Central the server is created, but az sql db create --use-free-limit true fails with ProvisioningDisabled. I'll use regular serverless databases (2 GB, 60-minute auto-pause) on a server in Spain Central, and note it in the README. Please tell me if you'd rather I do something else.
