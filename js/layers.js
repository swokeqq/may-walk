function setLayer(selectedLayer) {
  activeLayer = selectedLayer;

  if (selectedLayer === "osm") {
    activeLayerText.textContent = "OpenStreetMap";
    return;
  }

  if (selectedLayer === "google") {
    activeLayerText.textContent = "Google Maps (заглушка)";
    alert("Google Maps пока не подключены.");
    layerButtons.forEach((btn) => btn.classList.remove("active"));
    document.querySelector('.layer-btn[data-layer="osm"]').classList.add("active");
    activeLayer = "osm";
    activeLayerText.textContent = "OpenStreetMap";
  }

  if (selectedLayer === "yandex") {
    activeLayerText.textContent = "Яндекс Карты (заглушка)";
    alert("Яндекс Карты пока не подключены.");
    layerButtons.forEach((btn) => btn.classList.remove("active"));
    document.querySelector('.layer-btn[data-layer="osm"]').classList.add("active");
    activeLayer = "osm";
    activeLayerText.textContent = "OpenStreetMap";
  }
}