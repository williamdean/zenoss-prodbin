#
# Makefile for zenoss-version
#
.PHONY: clean-zenoss-version build-zenoss-version pkg-zenoss-version generate-zversion

ZENOSS_VERSION_BASE := legacy/zenoss-version
WHEEL_ARTIFACT := $(ZENOSS_VERSION_BASE)/dist/Zenoss-$(VERSION)-py2-none-any.whl

clean-zenoss-version:
	rm -f $(ZENOSS_VERSION_BASE)/setup.py
	rm -rf $(ZENOSS_VERSION_BASE)/src/Zenoss.egg-info
	rm -rf $(ZENOSS_VERSION_BASE)/build $(ZENOSS_VERSION_BASE)/dist

build-zenoss-version: mk-dist $(WHEEL_ARTIFACT)
	cp $(WHEEL_ARTIFACT) $(DIST_ROOT)

$(WHEEL_ARTIFACT): build-version-wheel

build-version-wheel: generate-zversion
	@echo "Building a binary distribution of zenoss-version"
	sed -e 's/%VERSION%/$(VERSION)/g' $(ZENOSS_VERSION_BASE)/setup.py.in > $(ZENOSS_VERSION_BASE)/setup.py
	$(DOCKER_RUN) "cd /mnt/$(ZENOSS_VERSION_BASE) && python setup.py bdist_wheel"

generate-zversion:
	@echo "generating ZVersion.py"
	sed -e 's/%VERSION_STRING%/$(VERSION)/g; s/%BUILD_NUMBER%/$(BUILD_NUMBER)/g' Products/ZenModel/ZVersion.py.in > Products/ZenModel/ZVersion.py
