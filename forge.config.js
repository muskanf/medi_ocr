// forge.config.js
const path = require("path");
const fs   = require("fs/promises");

module.exports = {
  packagerConfig: {
    asarUnpack: [
      "python_dist/**",        // our frozen exe
      "windows_tesseract/**",
      "dictionary/**"
    ]
  },
  makers: [{ name: "@electron-forge/maker-squirrel" }],

  hooks: {
    /**
     * After `npm run package` finishes, Forge gives us the paths
     * where Electron-Packager dropped the ready-to-zip app(s).
     */
    async postPackage(_forgeConfig, packageResult) {
      for (const pkgPath of packageResult.outputPaths) {
        const resources = path.join(pkgPath, "resources");

        // 1) PyInstaller output
        await fs.cp(
          path.join(__dirname, "python_dist"),
          path.join(resources, "python_dist"),
          { recursive: true }
        );

        // 2) Portable Tesseract
        await fs.cp(
          path.join(__dirname, "windows_tesseract"),
          path.join(resources, "windows_tesseract"),
          { recursive: true }
        );

        await fs.cp(
          path.join(__dirname, "dictionary"),
          path.join(resources, "dictionary"),
          { recursive: true }
        );
      }
    }
  }
};
