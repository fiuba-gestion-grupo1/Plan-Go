const formatDate = (dateStr) => {
  if (!dateStr) return null;
  const date = new Date(dateStr + "T00:00:00");
  return date.toISOString().split("T")[0];
};

const startDate = "2025-11-17";
const endDate = "2025-11-20";

console.log("Fecha inicial ingresada:", startDate);
console.log("Fecha final ingresada:", endDate);
console.log("Fecha inicial después del formateo:", formatDate(startDate));
console.log("Fecha final después del formateo:", formatDate(endDate));
console.log("\nDebugging detallado:");
console.log("Fecha inicial raw:", startDate);
console.log("Date object inicial:", new Date(startDate + "T00:00:00"));
console.log(
  "ISO string completo:",
  new Date(startDate + "T00:00:00").toISOString(),
);
console.log(
  "Solo fecha:",
  new Date(startDate + "T00:00:00").toISOString().split("T")[0],
);
