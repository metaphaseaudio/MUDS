#!/usr/bin/env python3
from pathlib import Path
import logging
import platform
from .util import run
from .plugin_build_config import PluginBuildConfig


def build(cfg: PluginBuildConfig, project_root: Path=Path.cwd()) -> Path:
    log = logging.getLogger("BUILD")

    src_dir = project_root / "src"
    build_dir = src_dir / "build-release"
    log.info(f"=== Building {cfg.plugin_name} ===")

    if not cfg.skip_web_ui:
        web_dir = cfg.web_dir or (src_dir / "plugin" / "gooey" / "web")
        log.info("Step 1: Building Web UI")
        if not (web_dir / "node_modules").is_dir():
            log.info("-- Installing npm dependencies...")
            run(["npm", "install"], cwd=web_dir)

        log.info(f"-- Building embedded web bundle... {web_dir}")
        run(["npm", "run", "build:embedded"], cwd=web_dir)
    else:
        log.info("Step 1: Skipping Web UI build (--skip-web-ui)")

    cmake_target = cfg.cmake_target or f"{cfg.plugin_name}_VST3"

    log.info("Step 2: Building C++ Plugin")
    build_dir.mkdir(parents=True, exist_ok=True)
    cmake_flags = [
        "cmake", "..",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCOPY_PLUGIN_AFTER_BUILD=OFF",
    ]
    if not cfg.skip_web_ui:
        cmake_flags.append("-DWM_DYNAMIC_WEB_CONTENT=OFF")
        cmake_flags.append("-DWM_WEBVIEW_DEBUG=OFF")
    if platform.system() == "Darwin":
        cmake_flags.append("-DCMAKE_OSX_ARCHITECTURES=x86_64;arm64")
    elif platform.system() == "Windows":
        cmake_flags.extend(["-G", "Ninja"])
    run(cmake_flags, cwd=build_dir)
    run(["cmake", "--build", ".", "--config", "Release", "--parallel", "--target", cmake_target], cwd=build_dir)

    # Step 3: Locate the built VST3
    vst3_bundle = build_dir / f"{cfg.plugin_name}_artefacts" / "Release" / "VST3" / f"{cfg.plugin_name}.vst3"


    if not vst3_bundle.is_dir():
        raise RuntimeError(f"BUILD FAILED: VST3 bundle not found at {vst3_bundle}")

    return vst3_bundle
