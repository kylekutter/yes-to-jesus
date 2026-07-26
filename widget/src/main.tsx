import { createRoot } from "react-dom/client";
import { YouVersionProvider, BibleCard } from "@youversion/platform-react-ui";

const APP_KEY = "geVqn5fdPpaEp06QTEUAdJvzn8V2Sc1numq2LfwpJREmAS0X";

function mountAll() {
  const nodes = document.querySelectorAll<HTMLElement>("[data-yv-widget]");
  nodes.forEach((node) => {
    const reference = node.getAttribute("data-reference");
    const defaultVersionId = Number(node.getAttribute("data-default-version-id") || "3034");
    if (!reference) return;
    const root = createRoot(node);
    root.render(
      <YouVersionProvider appKey={APP_KEY} theme="light">
        <BibleCard reference={reference} defaultVersionId={defaultVersionId} showVersionPicker />
      </YouVersionProvider>
    );
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", mountAll);
} else {
  mountAll();
}
