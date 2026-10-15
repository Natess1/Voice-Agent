import * as vscode from "vscode";
import * as http from "http";
import * as fs from "fs";
import * as path from "path";
import * as crypto from "crypto";

const MAX_SELECTION_CHARS = 20000;

function safeEqual(a: string, b: string): boolean {
  const left = Buffer.from(a);
  const right = Buffer.from(b);
  if (left.length !== right.length) {
    return false;
  }
  return crypto.timingSafeEqual(left, right);
}

function collectTabs() {
  const tabs: Array<{
    path: string;
    label: string;
    isActive: boolean;
    isDirty: boolean;
  }> = [];
  for (const group of vscode.window.tabGroups.all) {
    for (const tab of group.tabs) {
      if (tab.input instanceof vscode.TabInputText) {
        tabs.push({
          path: tab.input.uri.fsPath,
          label: tab.label,
          isActive: tab.isActive && group.isActive,
          isDirty: tab.isDirty,
        });
      }
    }
  }
  return tabs;
}

function collectContext() {
  const editor = vscode.window.activeTextEditor;
  const folders = (vscode.workspace.workspaceFolders ?? []).map(
    (folder) => folder.uri.fsPath,
  );
  let active: object | null = null;
  if (editor) {
    const selection = editor.selection;
    const selectedText = editor.document.getText(selection);
    active = {
      path: editor.document.uri.fsPath,
      languageId: editor.document.languageId,
      isDirty: editor.document.isDirty,
      lineCount: editor.document.lineCount,
      cursorLine: selection.active.line + 1,
      selection: {
        isEmpty: selection.isEmpty,
        startLine: selection.start.line + 1,
        endLine: selection.end.line + 1,
        text: selectedText.slice(0, MAX_SELECTION_CHARS),
        truncated: selectedText.length > MAX_SELECTION_CHARS,
      },
    };
  }
  return { workspaceFolders: folders, activeFile: active, tabs: collectTabs() };
}

function startServer(port: number, token: string): http.Server {
  const server = http.createServer((request, response) => {
    const sendJson = (status: number, body: unknown) => {
      const payload = JSON.stringify(body);
      response.writeHead(status, {
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": Buffer.byteLength(payload),
      });
      response.end(payload);
    };
    const provided = request.headers["x-agent-token"];
    if (typeof provided !== "string" || !safeEqual(provided, token)) {
      sendJson(401, { error: "unauthorized" });
      return;
    }
    if (request.method === "GET" && request.url === "/ping") {
      sendJson(200, { ok: true });
      return;
    }
    if (request.method === "GET" && request.url === "/context") {
      sendJson(200, collectContext());
      return;
    }
    sendJson(404, { error: "not found" });
  });
  server.on("error", (error: NodeJS.ErrnoException) => {
    if (error.code === "EADDRINUSE") {
      vscode.window.showErrorMessage(
        `Voice Agent Bridge: порт ${port} уже занят.`,
      );
    } else {
      vscode.window.showErrorMessage(
        `Voice Agent Bridge: ошибка сервера: ${error.message}`,
      );
    }
  });
  server.listen(port, "127.0.0.1", () => {
    vscode.window.showInformationMessage(
      `Voice Agent Bridge: сервер запущен на 127.0.0.1:${port}`,
    );
  });
  return server;
}

export function activate(context: vscode.ExtensionContext) {
  const config = vscode.workspace.getConfiguration("voiceAgent");
  const port = config.get<number>("port", 8765);
  const tokenFile = config.get<string>(
    "tokenFile",
    "D:\\voice-agent\\vscode_token.txt",
  );
  const token = crypto.randomBytes(24).toString("hex");
  try {
    fs.mkdirSync(path.dirname(tokenFile), { recursive: true });
    fs.writeFileSync(tokenFile, token, { encoding: "utf8" });
  } catch (error) {
    vscode.window.showErrorMessage(
      `Voice Agent Bridge: не удалось записать токен: ${String(error)}`,
    );
    return;
  }
  const server = startServer(port, token);
  context.subscriptions.push({ dispose: () => server.close() });
}

export function deactivate() {}
