#!/usr/bin/env bash

DOCSITE_DIR="docsite"
VENV_DIR="${DOCSITE_DIR}/venv"
BIN_DIR="${VENV_DIR}/bin"
RST_DIR="${DOCSITE_DIR}/rst"
BUILD_DIR="${DOCSITE_DIR}/build"
COLLECTIONS_DIR="${DOCSITE_DIR}/collections/ansible_collections/kowabunga"

rm -rf ${DOCSITE_DIR}
mkdir -p ${DOCSITE_DIR}
cp conf.py ${DOCSITE_DIR}

# Create Python virtual environment
python3 -m venv ${VENV_DIR}
${VENV_DIR}/bin/pip3 install antsibull-docs
${VENV_DIR}/bin/pip3 install Sphinx
${VENV_DIR}/bin/pip3 install sphinx-ansible-theme

cat <<EOF > ${DOCSITE_DIR}/ansible.cfg
[defaults]
ansible_python_interpreter = ./venv/bin/python3
collections_paths = ./collections/
EOF

mkdir -p ${COLLECTIONS_DIR}
ln -sf ../../../.. ${COLLECTIONS_DIR}/cloud

# Build RST documentation
mkdir -p ${RST_DIR}
mkdir -p ${BUILD_DIR}

cd ${DOCSITE_DIR}
ANSIBLE_CONFIG=ansible.cfg ./venv/bin/antsibull-docs collection --use-current --dest-dir rst kowabunga.cloud
./venv/bin/sphinx-build -M html rst/collections build -c . -W --keep-going
cd ..
