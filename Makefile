##
## EPITECH PROJECT, 2024
## video-code
## File description:
## Makefile
##

# >>> Variables <<<

BINARY_NAME		=	video-code
BUILD_DIR		=	build
DOCKER_IMG_NAME =   ubuntu-lts-img
VCPKG_VOLUME    =   video_code_vcpkg_cache

CMAKE_FLAGS		=	-G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
VCPKG_FLAGS		= \
	-DCMAKE_TOOLCHAIN_FILE=$$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake \
	-DVCPKG_INSTALLED_DIR=$(PWD)/vcpkg_installed \
	-DVCPKG_OVERLAY_PORTS=$(PWD)/vcpkg-overlay-ports \
	-DWITH_FFMPEG=ON

DEBUG_FLAG		=	-DDEBUG=ON
VERBOSE_FLAG	=	-DVC_VERBOSE=ON


# >>> Rules <<<

.PHONY: all
all: cmake


.PHONY: cmake
cmake:
	cmake -B $(BUILD_DIR) -DDEBUG=OFF -DVC_VERBOSE=OFF $(VCPKG_FLAGS) $(CMAKE_FLAGS)
	cmake --build $(BUILD_DIR)
	@ cp -f $(BUILD_DIR)/$(BINARY_NAME).app/Contents/MacOS/$(BINARY_NAME) .
	@ command -v codesign > /dev/null && codesign -f -s - $(BINARY_NAME) > /dev/null 2>&1 || true
	@ cp -f $(BUILD_DIR)/compile_commands.json .


.PHONY: debug
debug:
	cmake -B $(BUILD_DIR) $(DEBUG_FLAG) $(VCPKG_FLAGS) $(CMAKE_FLAGS)
	cmake --build $(BUILD_DIR)
	@ cp $(BUILD_DIR)/$(BINARY_NAME).app/Contents/MacOS/$(BINARY_NAME) .
	@ command -v codesign > /dev/null && codesign -f -s - $(BINARY_NAME) > /dev/null 2>&1 || true
	@ cp -f $(BUILD_DIR)/compile_commands.json .


.PHONY: verbose
verbose:
	cmake -B $(BUILD_DIR) -DDEBUG=OFF $(VERBOSE_FLAG) $(VCPKG_FLAGS) $(CMAKE_FLAGS)
	cmake --build $(BUILD_DIR)
	@ cp -f $(BUILD_DIR)/$(BINARY_NAME).app/Contents/MacOS/$(BINARY_NAME) .
	@ command -v codesign > /dev/null && codesign -f -s - $(BINARY_NAME) > /dev/null 2>&1 || true
	@ cp -f $(BUILD_DIR)/compile_commands.json .


.PHONY: clean
clean:
	@ $(RM) vgcore*


.PHONY: fclean
fclean: clean
	@ $(RM) -r $(BUILD_DIR)
	@ $(RM) -r vcpkg_installed
	@ $(RM) $(BINARY_NAME)


.PHONY: format
format:
	clang-format -i **/*.cpp **/*.hpp


# The gates GitHub cannot run: the goldens were rendered on this machine's GPU,
# and a shared runner's timings say nothing about a local baseline. Run it when
# you want the answer — never on the way to a push.
.PHONY: check
check:
	@ printf "\n→ visual regression (new failures only)\n"
	@# The run and the PARSE are two steps on purpose. They used to be one
	@# pipeline ending in `|| true`, so make saw awk's exit code and then
	@# discarded even that: a renderer that died on SIGSEGV printing nothing
	@# produced an empty failure list, which compares clean against an empty
	@# known_failures.txt. Measured — the recipe called 87 goldens green having
	@# rendered no pixels at all.
	@ ./video-code --visual-test > /tmp/vc_out.txt 2>&1; status=$$?; 		if [ $$status -gt 1 ]; then 			cat /tmp/vc_out.txt; 			printf "\033[31m--visual-test died (exit %s) — it did not finish, so nothing below means anything.\033[0m\n" "$$status"; 			exit 1; 		fi
	@ tr '\r' '\n' < /tmp/vc_out.txt | perl -pe 's/\e\[[0-9;]*m//g' \
		| awk '/^\[visual-test\]/ { scene = $$2 } /\[FAIL\]/ { print scene }' | sort -u \
		> /tmp/vc_failed.txt
	@ grep -v '^\#' test/visual/known_failures.txt | grep -v '^[[:space:]]*$$' | sort -u > /tmp/vc_known.txt
	@ if comm -23 /tmp/vc_failed.txt /tmp/vc_known.txt | grep -q .; then \
		printf "\033[31mgoldens moved that were passing:\033[0m\n"; \
		comm -23 /tmp/vc_failed.txt /tmp/vc_known.txt | sed 's/^/  /'; \
		printf "Look at the render before regenerating: a golden can be recording a bug.\n"; \
		exit 1; \
	fi
	@# And the other direction, which is how `matte` sat unlisted for a month:
	@# this recipe only ever reported failures it did NOT expect, so a list that
	@# was too SHORT was invisible, and a list that was too long would have been
	@# just as invisible. A tolerated failure that starts passing is good news
	@# nobody hears — and the entry left behind silently disarms that scene for
	@# the next real regression. The file's own header asks for this; nothing
	@# enforced it.
	@ if comm -13 /tmp/vc_failed.txt /tmp/vc_known.txt | grep -q .; then \
		printf "\033[31mknown_failures.txt is out of date - these pass now:\033[0m\n"; \
		comm -13 /tmp/vc_failed.txt /tmp/vc_known.txt | sed 's/^/  /'; \
		printf "Remove them: a stale entry disarms that scene for the next regression.\n"; \
		exit 1; \
	fi
	@ printf "  no new visual regressions, no stale exemptions\n"
	@ printf "\n→ C++ unit tests\n"
	@ cmake --build build --target video-code-tests > /dev/null && ./build/video-code-tests
	@ printf "\n→ what the scenes ask the renderer to do\n"
	@ python3 test/perf/digest.py
	@ printf "\n→ performance guard\n"
	@# --record: this machine is the only one that can measure a millisecond of
	@# this renderer, so the number is taken here and REMEMBERED in the commit.
	@# CI reads history.jsonl and draws the curve; it never measures.
	@ python3 test/perf/guard.py --record


# The hooks ship in the repo but git ignores them until it is told where they
# are, and nothing told it: `.githooks/pre-commit` sat unarmed since the day it
# was written. One command, per clone.
.PHONY: arm
arm:
	@ git config core.hooksPath .githooks
	@ printf "pre-commit armed — coverage, types and the QML chrome, ~15s\n"


.PHONY: docs
docs: cmake
docs: docvid
docs: docdoc


.PHONY: docvid
docvid:
	./$(BINARY_NAME) --generate


# Visual regression suite — golden-frame + hot-reload equivalence checks.
.PHONY: test
test:
	./$(BINARY_NAME) --visual-test


# (Re)write the golden images the suite compares against.
.PHONY: test-golden
test-golden:
	./$(BINARY_NAME) --visual-test --update-golden


# Python assertion-based unit tests.
.PHONY: test-unit
test-unit:
	./test/run_tests.sh


# Static type-checking for the Python API.
.PHONY: typecheck
typecheck:
	python3 -m pyright


# 1. Generate the Readme
# 2. Copies the generated video to example.gif
.PHONY: docdoc
docdoc:
	./docs/readme/generate.sh


# Doesn't work
.PHONY: docker
docker:
	$(MAKE) fclean
	docker build -t $(DOCKER_IMG_NAME) .
	docker run --rm -it \
		-v "$(PWD):/work" \
		$(DOCKER_IMG_NAME)
