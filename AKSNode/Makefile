# Node Problem Detector
NPD_VERSION=0.8.0
NPD_PACKAGE=node-problem-detector
NPD_ARCH?=amd64

DEB_DIR=deb
DEB_FILES = \
	$(NPD_PACKAGE)/$(NPD_PACKAGE)-v$(NPD_VERSION)-$(NPD_ARCH).deb

.PHONY: ALL
all: package

.PHONY: init
init:
	# Make this extensible and not just for NPD
	mkdir -p $(DEB_DIR)/$(NPD_PACKAGE)
	mkdir -p build

.PHONY: clean
clean:
	rm -rf build

define make-extension-zip
	$(eval NAME    = $(shell grep -oP "(?<=<Type>)[^<]+" manifest.xml))
	$(eval VERSION = $(shell grep -oP "(?<=<Version>)[^<]+" manifest.xml))

	@echo "Building '$(NAME)-$(VERSION).zip' ..."
	find . -type f | grep -v "/test/" | grep -v "./references" | zip -9 -@ build/$(NAME)-$(VERSION).zip > /dev/null
	@find ../Utils    -type f | grep -v "/test/"                | zip -9 -@ build/$(NAME)-$(VERSION).zip > /dev/null
endef

.PHONY: package
package: init $(DEB_DIR)/$(DEB_FILES)
	$(make-extension-zip)
	@cd ../Common/ && echo ./waagentloader.py           | zip -9 -@ ../AKSNode/build/$(NAME)-$(VERSION).zip > /dev/null
	@cd ../Common/WALinuxAgent-2.0.16 && echo ./waagent | zip -9 -@ ../../AKSNode/build/$(NAME)-$(VERSION).zip > /dev/null

$(DEB_DIR)/$(DEB_FILES):
	curl -fsSL https://akspackages.blob.core.windows.net/$(@:$(DEB_DIR)/%=%) -o $@
