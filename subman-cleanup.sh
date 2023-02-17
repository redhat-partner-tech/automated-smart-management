#!/bin/bash
yum clean all && rm -rf /var/cache/yum/* && subscription-manager remove --all && subscription-manager unregister && subscription-manager clean 



