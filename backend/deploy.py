import os
import shutil
import zipfile
import subprocess
import stat


def main():
    print("Creating Lambda deployment package...")

    # Clean up (handle files created by Docker as root)
    if os.path.exists("lambda-package"):

        def _on_rmtree_error(func, path, exc_info):
            try:
                os.chmod(path, 0o700)
            except Exception:
                pass
            func(path)

        shutil.rmtree("lambda-package", onerror=_on_rmtree_error)
    if os.path.exists("lambda-deployment.zip"):
        os.remove("lambda-deployment.zip")

    # Create package directory
    os.makedirs("lambda-package")

    # Install dependencies using Docker with Lambda runtime image
    print("Installing dependencies for Lambda runtime...")

    # Use the official AWS Lambda Python 3.12 image
    # This ensures compatibility with Lambda's runtime environment
    # Run Docker as the current user so files inside the mounted volume are
    # created with the host UID/GID instead of root.
    docker_cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{os.getcwd()}:/var/task",
        "--platform",
        "linux/amd64",
        "--entrypoint",
        "",
        "-u",
        f"{os.getuid()}:{os.getgid()}",
        "public.ecr.aws/lambda/python:3.12",
        "/bin/sh",
        "-c",
        "pip install --target /var/task/lambda-package -r /var/task/requirements.txt --timeout 240 --retries 5 --no-cache-dir --platform manylinux2014_x86_64 --only-binary=:all: --upgrade",
    ]

    subprocess.run(docker_cmd, check=True)

    # Copy application files
    print("Copying application files...")
    for file in [
        "server.py",
        "lambda_handler.py",
        "context.py",
        "resources.py",
        "digital_twin_agents.py",
        "config.py",
        "tools.py",
        "mcp_servers.py",
    ]:
        if os.path.exists(file):
            shutil.copy2(file, "lambda-package/")

    # Copy data directory
    if os.path.exists("data"):
        shutil.copytree("data", "lambda-package/data")

    if os.path.exists("prompts"):
        shutil.copytree("prompts", "lambda-package/prompts")

    if os.path.exists("public"):
        shutil.copytree("public", "lambda-package/public")

    if os.path.exists("models"):
        shutil.copytree("models", "lambda-package/models")

    if os.path.exists("utils"):
        shutil.copytree("utils", "lambda-package/utils")

    # Create zip
    print("Creating zip file...")
    with zipfile.ZipFile("lambda-deployment.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("lambda-package"):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, "lambda-package")
                zipf.write(file_path, arcname)

    # Show package size
    size_mb = os.path.getsize("lambda-deployment.zip") / (1024 * 1024)
    print(f"✓ Created lambda-deployment.zip ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
