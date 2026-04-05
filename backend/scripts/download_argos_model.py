"""Download and install the argostranslate nl→en model.

Run once during Docker image build (or local setup) to pre-install the
translation package so the application doesn't fetch it at runtime.
"""

import argostranslate.package

argostranslate.package.update_package_index()
pkgs = argostranslate.package.get_available_packages()
pkg = next((p for p in pkgs if p.from_code == "nl" and p.to_code == "en"), None)
assert pkg is not None, "argostranslate nl->en package not available"
argostranslate.package.install_from_path(pkg.download())
print("argostranslate nl→en model installed successfully")
