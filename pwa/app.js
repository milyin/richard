const list = document.querySelector("#lineList");
const template = document.querySelector("#lineTemplate");
const searchInput = document.querySelector("#searchInput");
const collapseButton = document.querySelector("#collapseButton");
const installButton = document.querySelector("#installButton");

let allLines = [];
let installPrompt = null;

const normalize = (value) => value.toLocaleLowerCase("ru-RU");

function render(lines) {
  list.replaceChildren();

  if (!lines.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "Ничего не найдено.";
    list.append(empty);
    return;
  }

  const fragment = document.createDocumentFragment();
  for (const line of lines) {
    const node = template.content.firstElementChild.cloneNode(true);
    node.classList.add(line.kind);
    node.dataset.id = line.id;

    const button = node.querySelector(".line-button");
    const speaker = node.querySelector(".speaker");
    const french = node.querySelector(".french");
    const translation = node.querySelector(".translation");
    const note = node.querySelector(".note");

    speaker.textContent = line.speaker;
    french.textContent = line.french;
    translation.textContent = line.russian;
    note.textContent = line.note;
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-label", line.speaker ? `${line.speaker}: ${line.french}` : line.french);

    button.addEventListener("click", () => {
      const expanded = node.classList.toggle("expanded");
      button.setAttribute("aria-expanded", String(expanded));
    });

    fragment.append(node);
  }
  list.append(fragment);
}

function filterLines() {
  const query = normalize(searchInput.value.trim());
  if (!query) {
    render(allLines);
    return;
  }

  render(
    allLines.filter((line) =>
      normalize(`${line.speaker} ${line.french} ${line.russian} ${line.note}`).includes(query),
    ),
  );
}

async function init() {
  const response = await fetch("data.json");
  if (!response.ok) {
    throw new Error(`Cannot load data.json: ${response.status}`);
  }

  const data = await response.json();
  allLines = data.lines;
  render(allLines);
}

searchInput.addEventListener("input", filterLines);

collapseButton.addEventListener("click", () => {
  for (const card of list.querySelectorAll(".line-card.expanded")) {
    card.classList.remove("expanded");
    card.querySelector(".line-button").setAttribute("aria-expanded", "false");
  }
});

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  installPrompt = event;
  installButton.hidden = false;
});

installButton.addEventListener("click", async () => {
  if (!installPrompt) return;
  installPrompt.prompt();
  await installPrompt.userChoice;
  installPrompt = null;
  installButton.hidden = true;
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js");
  });
}

init().catch((error) => {
  list.innerHTML = `<p class="empty-state">Ошибка загрузки приложения: ${error.message}</p>`;
});
