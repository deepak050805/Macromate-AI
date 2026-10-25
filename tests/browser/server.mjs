import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const child = spawn(
  process.env.PYTHON_EXECUTABLE || "python",
  [fileURLToPath(new URL("./server.py", import.meta.url))],
  { stdio: "inherit", windowsHide: true, env: { ...process.env, APP_ENV: "testing" } },
);
for (const signal of ["SIGINT", "SIGTERM"]) process.on(signal, () => child.kill(signal));
child.on("error", (error) => {
  console.error(error.message);
  process.exit(1);
});
child.on("exit", (code) => process.exit(code ?? 1));
