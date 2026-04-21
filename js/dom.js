const activeToolText = document.getElementById("activeToolText");
const activeLayerText = document.getElementById("activeLayerText");
const snapStatusText = document.getElementById("snapStatusText");

const snapToggle = document.getElementById("snapToggle");
const undoBtn = document.getElementById("undoBtn");
const redoBtn = document.getElementById("redoBtn");
const importBtn = document.getElementById("importBtn");
const exportBtn = document.getElementById("exportBtn");

const toolButtons = document.querySelectorAll(".tool-btn[data-tool]");
const layerButtons = document.querySelectorAll(".layer-btn");