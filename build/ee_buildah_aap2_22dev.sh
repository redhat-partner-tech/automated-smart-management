#!/bin/bash
set -ex

# podman login registry.redhat.io
# Username: {REGISTRY-SERVICE-ACCOUNT-USERNAME}
# Password: {REGISTRY-SERVICE-ACCOUNT-PASSWORD}
BASEIMAGEOWNER=ansible-automation-platform-22
BASEIMAGENAME=ee-supported-rhel8
BIVERSION=1.0.0-229
IMAGE=ee-automated-smart-mgmt-aap2-dev
VERSION=1.0.3
START_DIR=$(pwd)
TMP_WRKDIR=$(mktemp -d /tmp/XXXXXXXX)
COLLECTIONS_DIR=/usr/share/ansible/collections/ansible_collections
ctr=$(buildah from registry.redhat.io/$BASEIMAGEOWNER/$BASEIMAGENAME:$BIVERSION)
scratchmnt=$(buildah mount ${ctr})
buildah run $ctr /bin/sh -c 'python3 -m pip install jinja2==3.1.1'
buildah run $ctr /bin/sh -c 'python3 -m pip install apypie'
buildah run $ctr /bin/sh -c 'python3 -m pip install psycopg2-binary'
buildah run $ctr /bin/sh -c 'python3 -m pip install requests==2.28.1'
buildah run $ctr /bin/sh -c 'rm /usr/libexec/platform-python3.6'
buildah run $ctr /bin/sh -c 'ln -s /usr/bin/python3 /usr/libexec/platform-python3.6'
cd $TMP_WRKDIR
git clone https://github.com/redhat-partner-tech/automated-smart-management.git
cd automated-smart-management
git checkout ee-build-source-aap2-22-dev
buildah copy $ctr 'roles/content_views' '/usr/share/ansible/roles/content_views'
buildah copy $ctr 'roles/ec2_node_tools' '/usr/share/ansible/roles/ec2_node_tools'
buildah copy $ctr 'roles/rhsm_register' '/usr/share/ansible/roles/rhsm_register'
buildah copy $ctr 'roles/scap_client' '/usr/share/ansible/roles/scap_client'
buildah run $ctr /bin/sh -c '[ ! -d $COLLECTIONS_DIR/amazon/aws ] || rm -rf $COLLECTIONS_DIR/amazon/aws'
buildah run $ctr /bin/sh -c '[ ! -d $COLLECTIONS_DIR/ansible/controller ] || rm -rf $COLLECTIONS_DIR/ansible/controller'
buildah run $ctr /bin/sh -c '[ ! -d $COLLECTIONS_DIR/redhat_cop/controller_configuration ] || rm -rf $COLLECTIONS_DIR/redhat_cop/controller_configuration'
buildah run $ctr /bin/sh -c '[ ! -d $COLLECTIONS_DIR/redhat/satellite ] || rm -rf $COLLECTIONS_DIR/redhat/satellite'
buildah copy $ctr 'collections/ansible_collections/amazon/aws' \
	'$COLLECTIONS_DIR/amazon/'
buildah copy $ctr 'collections/ansible_collections/ansible/controller' \
	'$COLLECTIONS_DIR/ansible/'
buildah copy $ctr 'collections/ansible_collections/redhat_cop/controller_configuration' \
	'$COLLECTIONS_DIR/redhat_cop/'
buildah copy $ctr 'collections/ansible_collections/redhat/satellite' \
	'$COLLECTIONS_DIR/redhat/'
#buildah config --label name=${IMAGE} $ctr
cd $START_DIR
rm -rf $TMP_WRKDIR
buildah commit $ctr ${IMAGE}:${VERSION}
podman tag ${IMAGE}:${VERSION} ${IMAGE}:latest
buildah umount $ctr
buildah rm $ctr

# podman login quay.io
# podman push ${IMAGE}:${VERSION} quay.io/s4v0/${IMAGE}:${VERSION}
