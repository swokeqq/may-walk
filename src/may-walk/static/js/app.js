toolButtons.forEach((button) => {
  button.addEventListener("click", () => {
    toolButtons.forEach((btn) => btn.classList.remove("active"));
    button.classList.add("active");
    setTool(button.dataset.tool);
  });
});

layerButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const selectedLayer = button.dataset.layer;

    layerButtons.forEach((btn) => btn.classList.remove("active"));
    button.classList.add("active");

    setLayer(selectedLayer);
  });
});

snapToggle.addEventListener("change", () => {
  snapStatusText.textContent = snapToggle.checked ? "Включено" : "Выключено";
});

undoBtn.addEventListener("click", () => {
  alert("Отмена действия пока не реализована.");
});

redoBtn.addEventListener("click", () => {
  alert("Повтор действия пока не реализован.");
});

importBtn.addEventListener("click", () => {
  alert("Импорт GPX/KML/KMZ пока не реализован.");
});

exportBtn.addEventListener("click", () => {
  alert("Экспорт GPX/KML/KMZ пока не реализован.");
});

setTool("hand");
