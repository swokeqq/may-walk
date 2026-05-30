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

const authPasswordInput = document.getElementById("authPasswordInput");
const loginBtn = document.getElementById("loginBtn");
const logoutBtn = document.getElementById("logoutBtn");
const authStatusText = document.getElementById("authStatusText");
const authMessage = document.getElementById("authMessage");

const routeNameInput = document.getElementById("routeNameInput");
const newRouteBtn = document.getElementById("newRouteBtn");
const saveRouteBtn = document.getElementById("saveRouteBtn");
const deleteRouteBtn = document.getElementById("deleteRouteBtn");
const routesList = document.getElementById("routesList");
const routesMessage = document.getElementById("routesMessage");
const currentRouteText = document.getElementById("currentRouteText");

const exportModal = document.getElementById("exportModal");
const exportFormatSelect = document.getElementById("exportFormatSelect");
const confirmExportBtn = document.getElementById("confirmExportBtn");
const closeExportModalBtn = document.getElementById("closeExportModalBtn");

const asphaltDistanceText = document.getElementById("asphaltDistanceText");
const forestDistanceText = document.getElementById("forestDistanceText");
const fieldDistanceText = document.getElementById("fieldDistanceText");
const railDistanceText = document.getElementById("railDistanceText");
const otherDistanceText = document.getElementById("otherDistanceText");
const totalDistanceText = document.getElementById("totalDistanceText");
const snapRouteBtn = document.getElementById("snapRouteBtn");