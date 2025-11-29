import React, { useState, useEffect } from "react";
import { request } from "../utils/api";
import {
  PublicationAvailability,
  DurationBadge,
} from "../components/shared/AvailabilityComponents";
import PublicationCard from "../components/shared/PublicationCard";

export default function CustomItinerary({ me, token }) {
  console.log("\ud83c\udfa8 [COMPONENT] CustomItinerary renderizado");

  const [step, setStep] = useState("setup");
  console.log("\ud83c\udfaf [STATE] Step actual:", step);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [destination, setDestination] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [cantPersons, setCantPersons] = useState(1);
  const [budget, setBudget] = useState(0);
  const [itineraryData, setItineraryData] = useState(null);

  const [availablePublications, setAvailablePublications] = useState([]);
  const [selectedPublications, setSelectedPublications] = useState({});
  const [showPublicationModal, setShowPublicationModal] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState(null);

  const [showPasteModal, setShowPasteModal] = useState(false);
  const [aiItineraries, setAiItineraries] = useState([]);
  const [loadingAiItineraries, setLoadingAiItineraries] = useState(false);
  const [convertedFrom, setConvertedFrom] = useState(null);

  const [showPublicationDetailModal, setShowPublicationDetailModal] =
    useState(false);
  const [selectedPublication, setSelectedPublication] = useState(null);

  const [showErrorModal, setShowErrorModal] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const showPublicationDetail = (publication) => {
    setSelectedPublication(publication);
    setShowPublicationDetailModal(true);
  };

  const timeSlots = {
    morning: [
      "06:00",
      "06:30",
      "07:00",
      "07:30",
      "08:00",
      "08:30",
      "09:00",
      "09:30",
      "10:00",
      "10:30",
      "11:00",
      "11:30",
    ],
    afternoon: [
      "12:00",
      "12:30",
      "13:00",
      "13:30",
      "14:00",
      "14:30",
      "15:00",
      "15:30",
      "16:00",
      "16:30",
      "17:00",
      "17:30",
    ],
    evening: [
      "18:00",
      "18:30",
      "19:00",
      "19:30",
      "20:00",
      "20:30",
      "21:00",
      "21:30",
      "22:00",
      "22:30",
      "23:00",
      "23:30",
    ],
  };

  const periodLabels = {
    morning: "🌅 MAÑANA (6:00 - 12:00)",
    afternoon: "🌞 TARDE (12:00 - 18:00)",
    evening: "🌙 NOCHE (18:00 - 23:00)",
  };

  const generateDays = (start, end) => {
    const days = [];
    const startDate = new Date(start + "T12:00:00");
    const endDate = new Date(end + "T12:00:00");

    console.log("📅 [DEBUG] generateDays INPUT:", { start, end });
    console.log("📅 [DEBUG] generateDays PARSED:", { startDate, endDate });

    for (
      let d = new Date(startDate);
      d <= endDate;
      d.setDate(d.getDate() + 1)
    ) {
      days.push(new Date(d));
    }

    console.log("📅 [DEBUG] generateDays OUTPUT:", {
      daysGenerated: days.length,
    });
    console.log("📅 [DEBUG] Primera fecha:", days[0]?.toLocaleDateString());
    console.log(
      "📅 [DEBUG] Última fecha:",
      days[days.length - 1]?.toLocaleDateString(),
    );

    return days;
  };

  async function fetchPublications(
    destination,
    selectedDate = null,
    selectedTime = null,
  ) {
    console.log("🔍 Buscando publicaciones para destino:", destination);
    console.log("📅 Fecha seleccionada:", selectedDate);
    console.log("🕐 Horario seleccionado:", selectedTime);
    setLoading(true);
    try {
      const cityName = destination.includes(",")
        ? destination.split(",")[0].trim()
        : destination;
      console.log("🏙️ Ciudad extraída para búsqueda:", cityName);

      let url = `/api/publications/search?destination=${encodeURIComponent(cityName)}`;

      if (selectedDate && selectedTime) {
        url += `&date=${selectedDate}&time=${selectedTime}&persons=${cantPersons}`;
        console.log("✅ Aplicando filtros de disponibilidad");
      }

      console.log("🔍 URL de búsqueda:", url);
      console.log(
        "🔍 Token:",
        localStorage.getItem("token") ? "Presente" : "Ausente",
      );

      const data = await request(url, {
        token: localStorage.getItem("token"),
      });

      console.log("🔍 Respuesta de publicaciones:", data);
      console.log(
        "🔍 Cantidad de publicaciones encontradas:",
        data ? data.length : 0,
      );

      let filteredData = data || [];
      if (selectedDate && selectedTime && filteredData.length > 0) {
        console.log("🔍 Aplicando filtro de disponibilidad en frontend...");
        const dayOfWeek = new Date(selectedDate + "T00:00:00").getDay();
        const dayNamesShort = [
          "domingo",
          "lunes",
          "martes",
          "miércoles",
          "jueves",
          "viernes",
          "sábado",
        ];
        const dayName = dayNamesShort[dayOfWeek];
        console.log("📅 Día de la semana:", dayName);

        filteredData = filteredData.filter((pub) => {
          const availableDays = pub.available_days || [];
          console.log(
            `🔍 ${pub.place_name} - Días disponibles:`,
            availableDays,
          );
          const isDayAvailable =
            availableDays.length === 0 || availableDays.includes(dayName);

          const availableHours = pub.available_hours || [];
          console.log(
            `🔍 ${pub.place_name} - Horarios disponibles:`,
            availableHours,
          );
          const isTimeAvailable =
            availableHours.length === 0 ||
            availableHours.some((timeRange) => {
              const [start, end] = timeRange.split("-");
              const selectedTimeNumber = parseInt(
                selectedTime.replace(":", ""),
              );
              const startNumber = parseInt(start.replace(":", ""));
              const endNumber = parseInt(end.replace(":", ""));
              return (
                selectedTimeNumber >= startNumber &&
                selectedTimeNumber <= endNumber
              );
            });

          const isAvailable = isDayAvailable && isTimeAvailable;

          if (!isAvailable) {
            console.log(`❌ ${pub.place_name} no disponible:`, {
              dayAvailable: isDayAvailable,
              timeAvailable: isTimeAvailable,
              availableDays,
              availableHours,
              searchingFor: dayName,
              searchingTime: selectedTime,
            });
          } else {
            console.log(`✅ ${pub.place_name} disponible`);
          }

          return isAvailable;
        });

        console.log(
          `🔍 Publicaciones después del filtro: ${filteredData.length} de ${data.length}`,
        );
      }

      setAvailablePublications(filteredData);
    } catch (e) {
      console.error("❌ Error en búsqueda de publicaciones:", e);
      setError("Error al cargar publicaciones del destino");
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleSetupSubmit() {
    if (!destination || !startDate || !endDate) {
      setError("Por favor completa todos los campos");
      return;
    }

    const start = new Date(startDate);
    const end = new Date(endDate);

    if (start >= end) {
      setError("La fecha de inicio debe ser anterior a la fecha de fin");
      return;
    }

    const days = generateDays(startDate, endDate);

    if (days.length > 30) {
      setError("El itinerario no puede ser mayor a 30 días");
      return;
    }

    setError("");

    const itinerary = {};
    const daysWithKeys = days.map((day, index) => ({
      date: day,
      key: `day_${index + 1}`,
      index,
    }));

    daysWithKeys.forEach((dayObj) => {
      itinerary[dayObj.key] = {
        morning: {},
        afternoon: {},
        evening: {},
      };

      Object.keys(timeSlots).forEach((period) => {
        timeSlots[period].forEach((time) => {
          itinerary[dayObj.key][period][time] = null;
        });
      });
    });

    setItineraryData({ days: daysWithKeys, itinerary });
    await fetchPublications(destination);
    setStep("building");
  }

  const timeToMinutes = (timeStr) => {
    const [hours, minutes] = timeStr.split(":").map(Number);
    return hours * 60 + minutes;
  };

  const minutesToTime = (minutes) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours.toString().padStart(2, "0")}:${mins.toString().padStart(2, "0")}`;
  };

  const getAllTimeSlots = () => {
    return [...timeSlots.morning, ...timeSlots.afternoon, ...timeSlots.evening];
  };

  const calculateOccupiedSlots = (startTime, durationMinutes) => {
    const allSlots = getAllTimeSlots();
    const startIndex = allSlots.indexOf(startTime);
    if (startIndex === -1) return [startTime];

    const slotsNeeded = Math.ceil(durationMinutes / 30);
    const occupiedSlots = [];

    for (let i = 0; i < slotsNeeded && startIndex + i < allSlots.length; i++) {
      occupiedSlots.push(allSlots[startIndex + i]);
    }

    return occupiedSlots;
  };

  const getPeriodForTime = (time) => {
    if (timeSlots.morning.includes(time)) return "morning";
    if (timeSlots.afternoon.includes(time)) return "afternoon";
    if (timeSlots.evening.includes(time)) return "evening";
    return "morning";
  };

  const getSmartDuration = (publication) => {
    if (publication.duration_min && publication.duration_min > 0) {
      return publication.duration_min;
    }

    const categories = publication.categories || [];
    const categoryDurations = {
      museo: 180,
      restaurante: 90,
      teatro: 150,
      cine: 120,
      parque: 240,
      playa: 300,
      shopping: 180,
      mercado: 120,
      iglesia: 60,
      mirador: 90,
      bar: 120,
      cafe: 60,
      aventura: 240,
      deportes: 180,
      spa: 180,
      cultura: 150,
      gastronomia: 90,
      "vida-nocturna": 180,
    };

    for (const category of categories) {
      const categoryLower = (
        typeof category === "string"
          ? category
          : category.slug || category.name || ""
      ).toLowerCase();
      if (categoryDurations[categoryLower]) {
        return categoryDurations[categoryLower];
      }
    }

    return 120;
  };

  function addPublicationToSlot(publication) {
    setError("")
    try {
      console.log("🎯 [DEBUG] ==========================================");
      console.log("🎯 [DEBUG] addPublicationToSlot INICIADO!!!");
      console.log("🎯 [DEBUG] ==========================================");
      console.log("🎯 [DEBUG] addPublicationToSlot llamado con:", {
        publicationName: publication?.place_name,
        publicationId: publication?.id,
        selectedSlot: selectedSlot,
      });

      console.log("🚪 [DEBUG] Cerrando modal de actividades...");
      setShowPublicationModal(false);

      if (!selectedSlot) {
        console.error(
          "❌ [ERROR] selectedSlot es null/undefined:",
          selectedSlot,
        );
        alert(
          "Error: No se ha seleccionado un horario. Por favor, intenta de nuevo.",
        );
        return;
      }

      const { dayKey, period, time } = selectedSlot;
      console.log("🎯 [DEBUG] Slot seleccionado:", { dayKey, period, time });

      const durationMinutes = getSmartDuration(publication);
      console.log("⏱️ [DEBUG] Duración calculada:", durationMinutes, "minutos");

      const occupiedSlots = calculateOccupiedSlots(time, durationMinutes);
      console.log("📍 [DEBUG] Slots ocupados:", occupiedSlots);

      console.log(
        "🔍 [DEBUG] Verificando conflictos para slots:",
        occupiedSlots,
      );
      const conflictDetails = [];

      const hasConflict = occupiedSlots.some((slotTime) => {
        const slotPeriod = getPeriodForTime(slotTime);
        const existingActivity =
          itineraryData.itinerary[dayKey][slotPeriod][slotTime];
        console.log(
          `🔍 [CONFLICT CHECK] ${slotTime} en ${slotPeriod}:`,
          existingActivity,
        );

        const isConflict =
          existingActivity !== null && existingActivity !== undefined;

        if (isConflict) {
          console.log(
            `❌ [CONFLICT FOUND] Slot ${slotTime} está ocupado:`,
            existingActivity,
          );
          conflictDetails.push({
            slot: slotTime,
            period: slotPeriod,
            activity: existingActivity,
          });
        } else {
          console.log(`✅ [FREE SLOT] ${slotTime} está libre`);
        }

        return isConflict;
      });

      console.log("📋 [DEBUG] Detalles de conflictos:", conflictDetails);

      console.log("⚠️ [DEBUG] ¿Hay conflicto?", hasConflict);

      if (hasConflict) {
        console.error(
          "❌ [ERROR] Conflicto detectado - mostrando alerta detallada",
        );

        const conflictSlots = conflictDetails
          .map((c) => `${c.slot} (${c.activity.place_name || "Actividad"})`)
          .join(", ");
        const duration = Math.round((durationMinutes / 60) * 10) / 10;

        const detailedErrorMessage = `❌ Error al agregar actividad
      
📍 Actividad: ${publication.place_name}
⏱️ Duración: ${duration} horas (${durationMinutes} minutos)
🕐 Horario solicitado: ${time}
📅 Slots necesarios: ${occupiedSlots.join(", ")}

⚠️ CONFLICTOS DETECTADOS:
${conflictDetails.map((c) => `• ${c.slot}: ocupado por "${c.activity.place_name || c.activity}"`).join("\n")}

💡 Sugerencia: Elige un horario donde todos los slots estén libres o selecciona una actividad más corta.`;

        setErrorMessage(detailedErrorMessage);
        setShowErrorModal(true);
        return;
      }

      const activityData = {
        ...publication,
        duration_min: durationMinutes,
        start_time: time,
        is_main_slot: true,
      };

      console.log("📝 [DEBUG] Datos de actividad creados:", activityData);

      console.log("🔄 [DEBUG] Iniciando actualización de itineraryData...");
      setItineraryData((prev) => {
        console.log("📊 [DEBUG] Estado anterior:", prev);
        const newItinerary = { ...prev.itinerary };

        occupiedSlots.forEach((slotTime) => {
          const slotPeriod = getPeriodForTime(slotTime);
          console.log(
            `🔧 [DEBUG] Procesando slot ${slotTime} en periodo ${slotPeriod}`,
          );
          newItinerary[dayKey] = {
            ...newItinerary[dayKey],
            [slotPeriod]: {
              ...newItinerary[dayKey][slotPeriod],
              [slotTime]:
                slotTime === time
                  ? activityData
                  : {
                    ...publication,
                    duration_min: durationMinutes,
                    start_time: time,
                    is_continuation: true,
                    main_slot_time: time,
                  },
            },
          };
        });

        console.log("✅ [DEBUG] Nuevo itinerario creado:", newItinerary);
        const result = { ...prev, itinerary: newItinerary };
        console.log("📤 [DEBUG] Retornando estado actualizado:", result);
        return result;
      });

      setSelectedPublications((prev) => {
        const newSelected = { ...prev };
        occupiedSlots.forEach((slotTime) => {
          const slotPeriod = getPeriodForTime(slotTime);
          newSelected[`${dayKey}-${slotPeriod}-${slotTime}`] =
            slotTime === time
              ? activityData
              : {
                ...publication,
                is_continuation: true,
                main_slot_time: time,
              };
        });
        console.log(
          "📋 [DEBUG] selectedPublications actualizado:",
          newSelected,
        );
        return newSelected;
      });

      setSelectedSlot(null);

      console.log(
        "🎉 [SUCCESS] Actividad agregada exitosamente:",
        publication.place_name,
      );
    } catch (error) {
      console.error("💥 [ERROR] Error en addPublicationToSlot:", error);
      setErrorMessage(`Error al agregar actividad: ${error.message}`);
      setShowErrorModal(true);
    }
  }

  function removePublicationFromSlot(dayKey, period, time) {
    try {
      setError("");
      console.log("🗑️ [DEBUG] Intentando eliminar actividad:", {
        dayKey,
        period,
        time,
      });

      if (!itineraryData || !itineraryData.itinerary) {
        console.error("❌ itineraryData no disponible");
        return;
      }

      if (!itineraryData.itinerary[dayKey]) {
        console.error("❌ Día no encontrado:", dayKey);
        console.log(
          "🔍 Días disponibles:",
          Object.keys(itineraryData.itinerary),
        );
        return;
      }

      if (!itineraryData.itinerary[dayKey][period]) {
        console.error("❌ Período no encontrado:", period);
        return;
      }

      const currentActivity = itineraryData.itinerary[dayKey][period][time];
      console.log("🗑️ [DEBUG] Actividad actual:", currentActivity);

      if (!currentActivity) {
        console.log("❌ No se encontró actividad para eliminar");
        return;
      }

      const mainStartTime = currentActivity.is_continuation
        ? currentActivity.main_slot_time
        : time;
      console.log("🗑️ Tiempo de inicio principal:", mainStartTime);

      let mainActivity = currentActivity;
      if (currentActivity.is_continuation) {
        const mainPeriod = getPeriodForTime(mainStartTime);
        mainActivity =
          itineraryData.itinerary[dayKey][mainPeriod][mainStartTime];
        console.log("🗑️ Actividad principal encontrada:", mainActivity);
      }

      if (mainActivity && mainActivity.duration_min) {
        console.log(
          "🗑️ Actividad principal válida, duracion:",
          mainActivity.duration_min,
        );
        const occupiedSlots = calculateOccupiedSlots(
          mainStartTime,
          mainActivity.duration_min,
        );
        console.log("🗑️ Slots a limpiar:", occupiedSlots);

        setItineraryData((prev) => {
          console.log("🗑️ [DEBUG] Actualizando itineraryData...");
          const newItinerary = { ...prev.itinerary };

          occupiedSlots.forEach((slotTime) => {
            const slotPeriod = getPeriodForTime(slotTime);
            console.log(
              `🗑️ [DEBUG] Limpiando slot ${slotTime} en período ${slotPeriod}`,
            );
            newItinerary[dayKey] = {
              ...newItinerary[dayKey],
              [slotPeriod]: {
                ...newItinerary[dayKey][slotPeriod],
                [slotTime]: null,
              },
            };
          });

          console.log("🗑️ ✅ Actividad eliminada exitosamente!");
          return { ...prev, itinerary: newItinerary };
        });

        setSelectedPublications((prev) => {
          const newSelected = { ...prev };
          occupiedSlots.forEach((slotTime) => {
            const slotPeriod = getPeriodForTime(slotTime);
            delete newSelected[`${dayKey}-${slotPeriod}-${slotTime}`];
          });
          return newSelected;
        });

        console.log(
          `🎉 Actividad "${mainActivity.place_name || "Sin nombre"}" eliminada correctamente`,
        );
      } else {
        console.log(
          "🗑️ ❌ Actividad no tiene duration_min, eliminando solo este slot",
        );
        setItineraryData((prev) => ({
          ...prev,
          itinerary: {
            ...prev.itinerary,
            [dayKey]: {
              ...prev.itinerary[dayKey],
              [period]: {
                ...prev.itinerary[dayKey][period],
                [time]: null,
              },
            },
          },
        }));
        console.log("🗑️ ¡Slot eliminado exitosamente!");

        setSelectedPublications((prev) => {
          const newSelected = { ...prev };
          delete newSelected[`${dayKey}-${period}-${time}`];
          return newSelected;
        });
      }
    } catch (error) {
      console.error("🗑️ ❌ Error eliminando actividad:", error);
    }
  }

  const loadAiItineraries = async () => {
    setLoadingAiItineraries(true);
    try {
      console.log("🔍 Cargando itinerarios de IA...");
      console.log("📡 Token:", token ? "Presente" : "Ausente");
      const data = await request("/api/itineraries/ai-list", { token });
      console.log("📦 Respuesta completa del API:", data);
      console.log(
        "📊 Tipo de respuesta:",
        typeof data,
        "Es array:",
        Array.isArray(data),
      );

      let itineraries = data;
      if (data && typeof data === "object" && !Array.isArray(data)) {
        itineraries = data.itineraries || data.data || data.results || [];
        console.log("🔍 Extrayendo array del objeto. Resultado:", itineraries);
      }

      const finalItineraries = Array.isArray(itineraries) ? itineraries : [];
      console.log("✅ Cargados", finalItineraries.length, "itinerarios de IA");
      setAiItineraries(finalItineraries);
    } catch (error) {
      console.error("❌ Error cargando itinerarios de IA:", error);
      setAiItineraries([]);
    } finally {
      setLoadingAiItineraries(false);
    }
  };

  const pasteAiItinerary = async (aiItinerary) => {
    try {
      console.log("📋 Convirtiendo itinerario de IA:", aiItinerary.destination);

      const conversionData = {
        ai_itinerary_id: aiItinerary.id,
        custom_destination: destination || aiItinerary.destination,
        custom_start_date: startDate,
        custom_end_date: endDate,
      };

      console.log("📤 Enviando datos de conversión:", conversionData);
      const result = await request("/api/itineraries/convert-ai-to-custom", {
        method: "POST",
        token,
        body: conversionData,
      });

      console.log(
        "\ud83d\udce6 Respuesta completa del API conversión:",
        result,
      );
      console.log("\ud83d\udd0d Estructura de result:", {
        hasDestination: !!result.destination,
        hasStartDate: !!result.start_date,
        hasEndDate: !!result.end_date,
        hasDays: !!result.days,
        hasItinerary: !!result.itinerary,
        success: result.success,
      });

      console.log("🔍 ANÁLISIS DETALLADO DEL ITINERARIO RECIBIDO:");
      console.log("📅 Days array:", result.days);
      console.log(
        "📋 Itinerary object keys:",
        Object.keys(result.itinerary || {}),
      );

      if (result.itinerary) {
        Object.entries(result.itinerary).forEach(([dayKey, dayData]) => {
          const totalActivities = Object.values(dayData).reduce(
            (sum, period) => sum + Object.keys(period).length,
            0,
          );
          console.log(`📆 ${dayKey}: ${totalActivities} actividades`);
          Object.entries(dayData).forEach(([period, activities]) => {
            if (Object.keys(activities).length > 0) {
              console.log(
                `  🕐 ${period}: ${Object.keys(activities).length} slots`,
              );
              Object.entries(activities).forEach(([time, activity]) => {
                console.log(
                  `    ⏰ ${time}: ${activity.place_name || "Sin título"}`,
                );
              });
            }
          });
        });
      }

      console.log("\ud83d\udd04 Estableciendo itineraryData...");
      setItineraryData(result);
      console.log(
        "\ud83d\udd04 Estableciendo destination:",
        result.destination,
      );
      setDestination(result.destination);
      console.log("\ud83d\udd04 Estableciendo startDate:", result.start_date);
      setStartDate(result.start_date);
      console.log("\ud83d\udd04 Estableciendo endDate:", result.end_date);
      setEndDate(result.end_date);

      setCantPersons(result.cant_persons ?? aiItinerary.cant_persons ?? 1);
      setBudget(result.budget ?? aiItinerary.budget ?? 0);

      console.log("\ud83d\udd04 Estableciendo convertedFrom...");
      setConvertedFrom(aiItinerary);

      console.log(
        "🔍 Cargando publicaciones para destino:",
        result.destination,
      );
      await fetchPublications(result.destination);

      console.log("\ud83d\udd04 Cerrando modal y cambiando a building...");
      setShowPasteModal(false);
      setStep("building");

      console.log(
        "\ud83c\udf89 Todos los estados establecidos. Step actual:",
        "building",
      );

      console.log("🎉 Itinerario de IA pegado exitosamente");
    } catch (error) {
      console.error("❌ Error convirtiendo itinerario:", error);
      setError("Error al pegar el itinerario de IA: " + error.message);
    }
  };

  const formatDate = (date) => {
    return date.toLocaleDateString("es-ES", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  async function saveItinerary() {
    console.log("💾 [DEBUG] Iniciando guardado del itinerario...");
    console.log("💾 [DEBUG] Estado actual:");
    console.log("  - Destino:", destination);
    console.log("  - Fechas:", startDate, "a", endDate);
    console.log(
      "  - Personas:",
      cantPersons,
      "(tipo:",
      typeof cantPersons,
      ")",
    );
    console.log("  - Presupuesto:", budget, "(tipo:", typeof budget, ")");

    setLoading(true);
    setError("");

    try {
      const payload = {
        destination,
        start_date: startDate,
        end_date: endDate,
        cant_persons: cantPersons,
        budget: budget,
        itinerary_data: itineraryData.itinerary,
        type: "custom",
      };

      console.log(
        "💾 [DEBUG] Payload completo:",
        JSON.stringify(payload, null, 2),
      );
      console.log(
        "💾 [DEBUG] Token:",
        localStorage.getItem("token") ? "Presente" : "No encontrado",
      );
      console.log("💾 [DEBUG] URL del endpoint: /api/itineraries/custom");

      const response = await request("/api/itineraries/custom", {
        method: "POST",
        token: localStorage.getItem("token"),
        body: payload,
      });

      console.log("✅ [DEBUG] Respuesta del servidor:", response);

      alert("¡Itinerario personalizado guardado exitosamente!");

      if (response && response.id) {
        console.log(
          "💾 [DEBUG] Guardando ID del itinerario para mostrar:",
          response.id,
        );
        localStorage.setItem("showItineraryId", response.id.toString());
        console.log(
          "🔗 [DEBUG] Redirigiendo a mis itinerarios con ID:",
          response.id,
        );
        window.location.href = `/?view=my-itineraries&showId=${response.id}`;
      } else {
        console.log(
          "🔗 [DEBUG] Sin ID de respuesta, redirigiendo a mis itinerarios",
        );
        window.location.href = "/?view=my-itineraries";
      }
    } catch (e) {
      console.error("❌ [ERROR] Error completo:", e);
      console.error("❌ [ERROR] Stack trace:", e.stack);
      console.error("❌ [ERROR] Message:", e.message);

      let errorMessage = "Error al guardar el itinerario";

      if (
        e.message &&
        e.message.includes("NO ES POSIBLE GUARDAR EL ITINERARIO")
      ) {
        errorMessage = e.message.replace(/^\s*\d+\s*:\s*/g, "");
        setError(errorMessage);

        const validationModal = document.createElement("div");
        validationModal.className = "modal fade";
        validationModal.style.zIndex = "2000";
        validationModal.innerHTML = `
          <div class="modal-dialog modal-lg">
            <div class="modal-content">
              <div class="modal-header bg-danger text-white">
                <h5 class="modal-title">❌ Error de Validación</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
              </div>
              <div class="modal-body">
                <div style="white-space: pre-line; font-family: monospace; background: #f8f9fa; padding: 15px; border-radius: 5px; max-height: 400px; overflow-y: auto;">
                  ${errorMessage}
                </div>
                <div class="mt-3">
                  <h6>📋 Para resolver estos problemas:</h6>
                  <ul>
                    <li>Verifica que todas las actividades estén disponibles en los días seleccionados</li>
                    <li>Revisa los horarios de disponibilidad de cada actividad</li>
                    <li>Asegúrate de que el presupuesto cubra todos los costos</li>
                    <li>Elimina actividades problemáticas y vuelve a agregarlas</li>
                  </ul>
                </div>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-primary" data-bs-dismiss="modal">
                  🔧 Entendido, voy a corregir
                </button>
              </div>
            </div>
          </div>
        `;

        document.body.appendChild(validationModal);
        const modal = new window.bootstrap.Modal(validationModal);
        modal.show();

        validationModal.addEventListener("hidden.bs.modal", () => {
          document.body.removeChild(validationModal);
        });

        return;
      } else {
        if (e.message) {
          errorMessage += ": " + e.message;
        }
        if (e.status) {
          errorMessage += ` (HTTP ${e.status})`;
        }

        setError(errorMessage);
        //alert(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  }

  console.log(
    "\ud83c\udfaf [RENDER] Evaluando condiciones de renderizado. Step:",
    step,
    "ItineraryData:",
    !!itineraryData,
  );

  if (step === "setup") {
    console.log("\ud83c\udfe0 [RENDER] Renderizando setup step");
    return (
      <div className="container mt-4">
        <div className="row justify-content-center">
          <div className="col-lg-6">
            <div className="text-center mb-4">
              <h3 className="mb-3">✏️ Crear Itinerario Personalizado</h3>
              <p className="text-muted">
                Configura los detalles básicos para comenzar a armar tu
                itinerario
              </p>
            </div>

            {error && <div className="alert alert-danger">{error}</div>}

            <div className="card shadow-sm">
              <div className="card-body">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSetupSubmit();
                  }}
                >
                  <div className="mb-3">
                    <label className="form-label">
                      <strong>📍 Destino</strong>
                    </label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Ej: Buenos Aires, Argentina"
                      value={destination}
                      onChange={(e) => setDestination(e.target.value)}
                      required
                    />
                    <small className="text-muted">
                      Solo se mostrarán publicaciones de este destino
                    </small>
                  </div>

                  <div className="row">
                    <div className="col-md-6">
                      <div className="mb-3">
                        <label className="form-label">
                          <strong>📅 Fecha de inicio</strong>
                        </label>
                        <input
                          type="date"
                          className="form-control"
                          value={startDate}
                          onChange={(e) => setStartDate(e.target.value)}
                          min={new Date().toISOString().split("T")[0]}
                          required
                        />
                      </div>
                    </div>
                    <div className="col-md-6">
                      <div className="mb-3">
                        <label className="form-label">
                          <strong>📅 Fecha de fin</strong>
                        </label>
                        <input
                          type="date"
                          className="form-control"
                          value={endDate}
                          onChange={(e) => setEndDate(e.target.value)}
                          min={
                            startDate || new Date().toISOString().split("T")[0]
                          }
                          required
                        />
                      </div>
                    </div>
                  </div>

                  <div className="row">
                    <div className="col-md-6">
                      <div className="mb-3">
                        <label className="form-label">
                          <strong>👥 Cantidad de personas</strong>
                        </label>
                        <input
                          type="number"
                          className="form-control"
                          value={cantPersons}
                          onChange={(e) => {
                            const value = parseInt(e.target.value) || 1;
                            console.log(
                              "👥 [DEBUG] Cambiando personas a:",
                              value,
                            );
                            setCantPersons(value);
                          }}
                          min="1"
                          max="20"
                          required
                        />
                      </div>
                    </div>
                    <div className="col-md-6">
                      <div className="mb-3">
                        <label className="form-label">
                          <strong>💰 Presupuesto estimado (USD)</strong>
                        </label>
                        <input
                          type="number"
                          className="form-control"
                          value={budget}
                          onChange={(e) => {
                            const value = parseInt(e.target.value) || 0;
                            console.log(
                              "💰 [DEBUG] Cambiando presupuesto a:",
                              value,
                            );
                            setBudget(value);
                          }}
                          min="0"
                          placeholder="Presupuesto en USD"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="d-grid gap-2">
                    <button
                      type="submit"
                      className="btn btn-outline-custom"
                      disabled={loading}
                    >
                      {loading ? "Preparando..." : "Continuar"}
                    </button>

                    <div className="text-center my-2">
                      <small className="text-muted">o</small>
                    </div>

                    <button
                      type="button"
                      className="btn btn-outline-info"
                      onClick={() => {
                        console.log('🖱️ Botón "Pegar IA" clickeado');
                        console.log(
                          "🎯 Estado actual showPasteModal:",
                          showPasteModal,
                        );
                        loadAiItineraries();
                        setShowPasteModal(true);
                        console.log("🎯 setShowPasteModal(true) ejecutado");
                        setTimeout(() => {
                          console.log(
                            "🎯 Estado showPasteModal después de setTimeout:",
                            showPasteModal,
                          );
                        }, 100);
                      }}
                      disabled={loading}
                    >
                      📋 Modifica un itinerario existente
                    </button>
                  </div>
                </form>
              </div>
            </div>

            <div className="text-center mt-3">
              <small className="text-muted">
                💡 Podrás agregar actividades personalizadas y elegir horarios
                específicos para cada día
              </small>
            </div>
          </div>
        </div>

        {console.log(
          "🎯 [RENDER] Evaluando condición modal (dentro de setup):",
          showPasteModal,
          typeof showPasteModal,
        )}
        {showPasteModal && (
          <div
            className="modal show d-block"
            style={{ backgroundColor: "rgba(0,0,0,0.5)" }}
          >
            {console.log(
              "🎯 [RENDER] Modal de Pegar IA renderizándose desde setup!",
            )}
            <div className="modal-dialog modal-lg">
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">📋 Pegar Itinerario de IA</h5>
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => setShowPasteModal(false)}
                  ></button>
                </div>
                <div className="modal-body">
                  {loadingAiItineraries ? (
                    <div className="text-center p-4">
                      <div
                        className="spinner-border"
                        style={{ color: "#3A92B5" }}
                        role="status"
                      >
                        <span className="visually-hidden">Cargando...</span>
                      </div>
                      <p className="mt-2">Cargando tus itinerarios de IA...</p>
                    </div>
                  ) : aiItineraries.length === 0 ? (
                    <div className="text-center p-4">
                      <i className="bi bi-inbox fs-1 text-muted"></i>
                      <h6 className="mt-3">No tienes itinerarios de IA</h6>
                      <p className="text-muted">
                        Primero debes crear un itinerario usando IA para poder
                        pegarlo aquí.
                      </p>
                    </div>
                  ) : (
                    <div>
                      <p className="text-muted mb-3">
                        Selecciona uno de tus itinerarios de IA para pegarlo en
                        el constructor personalizado:
                      </p>
                      <div className="row g-3">
                        {aiItineraries
                          .filter((itinerary) => {
                            // 🔥 Solo excluir itinerarios personalizados
                            if (!itinerary.trip_type) return true;

                            const type = itinerary.trip_type.toLowerCase();

                            return type !== "personalizado" && type !== "custom";
                          })
                          .map((itinerary) => (
                            <div key={itinerary.id} className="col-12">
                              <div
                                className="card border hover-card"
                                style={{ cursor: "pointer" }}
                                onClick={() => pasteAiItinerary(itinerary)}
                              >

                                <div className="card-body">
                                  <div className="d-flex justify-content-between align-items-start">
                                    <div className="flex-grow-1">
                                      <h6 className="card-title mb-1">
                                        📍 {itinerary.destination}
                                      </h6>
                                      <div className="mb-2">
                                        <small className="text-muted">
                                          📅 {itinerary.duration_days} día(s) • 💰
                                          US${itinerary.budget} • 👥{" "}
                                          {itinerary.cant_persons} persona(s) • 🎨{" "}
                                          {itinerary.trip_type}
                                        </small>
                                      </div>
                                      <p className="card-text text-muted small mb-1">
                                        {itinerary.preview}
                                      </p>
                                      <div className="d-flex gap-2 align-items-center">
                                        <span
                                          className={`badge ${itinerary.status === "completed"
                                            ? "bg-success"
                                            : "bg-warning"
                                            }`}
                                        >
                                          {itinerary.status === "completed"
                                            ? "✅ Completo"
                                            : "⚠️ Con advertencias"}
                                        </span>
                                        {itinerary.has_validation && (
                                          <span className="badge bg-info">
                                            🔍 Validado
                                          </span>
                                        )}
                                        <span className="badge bg-light text-dark">
                                          🏛️ {itinerary.publication_count} lugares
                                        </span>
                                      </div>
                                    </div>
                                    <div className="text-end">
                                      <small className="text-muted">
                                        {new Date(
                                          itinerary.created_at,
                                        ).toLocaleDateString("es-ES")}
                                      </small>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
                <div className="modal-footer">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setShowPasteModal(false)}
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  if (step === "building" && itineraryData) {
    console.log("\ud83d\udee0\ufe0f [RENDER] Renderizando building step");
    console.log("\ud83d\udee0\ufe0f [RENDER] ItineraryData:", itineraryData);
    return (
      <div className="container mt-4">
        <div className="d-flex align-items-center justify-content-between mb-4">
          <div>
            <h3 className="mb-1">✏️ Itinerario Personalizado</h3>
            <p className="text-muted mb-0">
              📍 {destination} • {itineraryData.days.length} día(s)
            </p>
          </div>
          <div className="d-flex gap-2">
            <button
              className="btn btn-outline-secondary"
              onClick={() => setStep("setup")}
            >
              ← Volver a configuración
            </button>
            <button
              className="btn btn-success"
              onClick={saveItinerary}
              disabled={loading}
            >
              {loading ? "Guardando..." : "💾 Guardar Itinerario"}
            </button>
          </div>
        </div>

        {error && <div className="alert alert-danger">{error}</div>}

        {itineraryData.days.map((day, dayIndex) => {
          let dayKey, dayDate;
          if (typeof day === "string") {
            dayKey = day;
            dayDate = new Date(day);
          } else if (day && day.date) {
            dayKey = day.date;
            dayDate = new Date(day.date);
          } else if (day && day.toISOString) {
            dayKey = day.toISOString().split("T")[0];
            dayDate = day;
          } else {
            console.error("❌ Formato de día no reconocido:", day);
            return null;
          }

          const dayData =
            itineraryData.itinerary[`day_${dayIndex + 1}`] ||
            itineraryData.itinerary[dayKey] ||
            {};
          const actualDayKey = `day_${dayIndex + 1}`;

          return (
            <div key={dayKey} className="mb-5">
              <div className="card shadow-sm">
                <div
                  className="card-header text-white"
                  style={{ backgroundColor: "#3A92B5" }}
                >
                  <h5 className="mb-0">
                    DÍA {dayIndex + 1} - {formatDate(dayDate)}
                  </h5>
                </div>
                <div className="card-body">
                  {Object.entries(periodLabels).map(([period, label]) => (
                    <div key={period} className="mb-4">
                      <h6 className="mb-3 border-bottom pb-2">{label}</h6>

                      <div className="row g-2">
                        {timeSlots[period].map((time) => {
                          const publication = dayData[period][time];
                          const slotKey = `${actualDayKey}-${period}-${time}`;

                          return (
                            <div key={time} className="col-md-6 col-lg-4">
                              <div
                                className={`card h-100 ${publication ? (publication.is_continuation ? "border-warning bg-warning bg-opacity-10" : "border-success bg-light") : "border-light"}`}
                              >
                                <div className="card-body p-3">
                                  <div className="d-flex align-items-center justify-content-between mb-2">
                                    <strong style={{ color: "#3A92B5" }}>
                                      {time}
                                    </strong>
                                    {publication &&
                                      !publication.is_continuation && (
                                        <button
                                          className="btn btn-sm btn-outline-danger"
                                          onClick={() =>
                                            removePublicationFromSlot(
                                              actualDayKey,
                                              period,
                                              time,
                                            )
                                          }
                                          title="Remover actividad completa"
                                        >
                                          ×
                                        </button>
                                      )}
                                  </div>

                                  {publication ? (
                                    <div>
                                      {publication.is_continuation ? (
                                        <div className="text-center text-muted">
                                          <small>
                                            <em>↳ Continuación de:</em>
                                            <br />
                                            <strong>
                                              {publication.place_name}
                                            </strong>
                                            <br />
                                            <small>
                                              Inicio:{" "}
                                              {publication.start_time ||
                                                publication.main_slot_time}
                                            </small>
                                          </small>
                                        </div>
                                      ) : (
                                        <>
                                          <div className="mb-2">
                                            <strong className="d-block">
                                              {publication.place_name}
                                            </strong>
                                            {publication.duration_min && (
                                              <span className="badge bg-info text-white me-2">
                                                {Math.floor(
                                                  publication.duration_min / 60,
                                                )}
                                                h{" "}
                                                {publication.duration_min % 60}m
                                              </span>
                                            )}
                                            {publication.converted_from_ai && (
                                              <span className="badge bg-success text-white">
                                                De IA
                                              </span>
                                            )}
                                          </div>

                                          <button
                                            className="btn btn-sm btn-outline-info w-100"
                                            onClick={() =>
                                              showPublicationDetail(publication)
                                            }
                                          >
                                            🔍 Ver detalle
                                          </button>
                                        </>
                                      )}
                                    </div>
                                  ) : (
                                    <div className="text-center">
                                      <button
                                        className="btn btn-sm btn-outline-custom"
                                        onClick={async () => {
                                          console.log(
                                            "🎯 Abriendo modal para agregar actividad",
                                          );
                                          setSelectedSlot({
                                            dayKey: actualDayKey,
                                            period,
                                            time,
                                          });

                                          const dayDate =
                                            itineraryData.days.find(
                                              (d) => d.key === actualDayKey,
                                            )?.date;
                                          const dayDateString = dayDate
                                            ? dayDate
                                              .toISOString()
                                              .split("T")[0]
                                            : null;
                                          console.log(
                                            "📅 Fecha del slot:",
                                            dayDate,
                                          );
                                          console.log(
                                            "📅 Fecha como string:",
                                            dayDateString,
                                          );
                                          console.log(
                                            "🕐 Horario del slot:",
                                            time,
                                          );
                                          console.log(
                                            "👥 Personas:",
                                            cantPersons,
                                          );

                                          if (dayDateString && time) {
                                            console.log(
                                              "🔍 Buscando con filtros de disponibilidad...",
                                            );
                                            await fetchPublications(
                                              destination,
                                              dayDateString,
                                              time,
                                            );
                                          } else {
                                            console.log(
                                              "⚠️ Sin filtros de disponibilidad - búsqueda general",
                                            );
                                            await fetchPublications(
                                              destination,
                                            );
                                          }

                                          setShowPublicationModal(true);
                                        }}
                                      >
                                        + Agregar actividad
                                      </button>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}

        {showPublicationDetailModal && selectedPublication && (
          <div
            className="modal show d-block"
            tabIndex="-1"
            style={{ backgroundColor: "rgba(0,0,0,0.5)", zIndex: 1060 }}
          >
            <div className="modal-dialog modal-lg modal-dialog-centered">
              <div className="modal-content">
                <div className="modal-header">
                  <div>
                    <h5 className="modal-title mb-1">
                      📍 {selectedPublication.place_name}
                    </h5>
                    <small className="text-muted">
                      {selectedPublication.start_time &&
                        selectedPublication.end_time
                        ? `🕐 ${selectedPublication.start_time} - ${selectedPublication.end_time}`
                        : `⏱️ ${Math.floor(selectedPublication.duration_min / 60)}h ${selectedPublication.duration_min % 60}m`}
                    </small>
                  </div>
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => {
                      setShowPublicationDetailModal(false);
                      setSelectedPublication(null);
                    }}
                  />
                </div>
                <div
                  className="modal-body"
                  style={{ maxHeight: "70vh", overflowY: "auto" }}
                >
                  <PublicationCard
                    publication={selectedPublication}
                    carouselPrefix={`detail-${selectedPublication.id}`}
                    showRating={true}
                    showDetails={true}
                    footer={
                      <div className="mt-3">
                        {selectedPublication.converted_from_ai &&
                          selectedPublication.original_text && (
                            <div className="alert alert-info mb-3">
                              <div className="d-flex align-items-center mb-2">
                                <span className="me-2">🤖</span>
                                <strong>Descripción generada por IA:</strong>
                              </div>
                              <em>"{selectedPublication.original_text}"</em>
                            </div>
                          )}
                        {selectedPublication.description &&
                          selectedPublication.description !==
                          selectedPublication.original_text && (
                            <div className="mb-3">
                              <strong>📝 Descripción completa:</strong>
                              <p
                                className="mb-0 mt-1"
                                style={{ lineHeight: 1.5 }}
                              >
                                {selectedPublication.description}
                              </p>
                            </div>
                          )}
                        <div className="row">
                          {selectedPublication.cost_per_day && (
                            <div className="col-md-6 mb-2">
                              <strong>💰 Costo estimado:</strong>
                              <br />
                              <span className="badge bg-success">
                                ${selectedPublication.cost_per_day} por día
                              </span>
                            </div>
                          )}
                          {selectedPublication.duration_min && (
                            <div className="col-md-6 mb-2">
                              <strong>⏱️ Duración programada:</strong>
                              <br />
                              <span className="badge bg-info">
                                {Math.floor(
                                  selectedPublication.duration_min / 60,
                                )}
                                h {selectedPublication.duration_min % 60}m
                              </span>
                            </div>
                          )}
                        </div>
                        {selectedPublication.categories &&
                          selectedPublication.categories.length > 0 && (
                            <div className="mt-3">
                              <strong>🏷️ Categorías:</strong>
                              <div className="mt-1">
                                {selectedPublication.categories.map(
                                  (cat, idx) => (
                                    <span
                                      key={idx}
                                      className="badge bg-secondary me-1 mb-1"
                                    >
                                      {typeof cat === "string"
                                        ? cat
                                        : cat.name || cat.slug}
                                    </span>
                                  ),
                                )}
                              </div>
                            </div>
                          )}
                      </div>
                    }
                  />
                </div>
                <div className="modal-footer">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => {
                      setShowPublicationDetailModal(false);
                      setSelectedPublication(null);
                    }}
                  >
                    Cerrar
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {showPublicationModal && (
          <div
            className="modal show d-block"
            tabIndex="-1"
            style={{ backgroundColor: "rgba(0,0,0,0.5)" }}
          >
            <div className="modal-dialog modal-lg">
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">
                    Agregar actividad para {selectedSlot?.time}
                  </h5>
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => {
                      setShowPublicationModal(false);
                      setSelectedSlot(null);
                    }}
                  />
                </div>
                <div className="modal-body">
                  {loading ? (
                    <div className="text-center py-4">
                      <div className="spinner-border" role="status" />
                      <div>Cargando publicaciones...</div>
                    </div>
                  ) : availablePublications.length === 0 ? (
                    <div className="text-center py-4 text-muted">
                      <p>
                        No hay publicaciones disponibles para "{destination}"
                      </p>
                      <small>Intenta con un destino diferente</small>
                    </div>
                  ) : (
                    <div className="row g-3">
                      {availablePublications.map((pub) => (
                        <div key={pub.id} className="col-md-6">
                          <div className="card h-100 border-primary">
                            {pub.photos && pub.photos.length > 0 && (
                              <img
                                src={pub.photos[0]}
                                className="card-img-top"
                                alt={pub.place_name}
                                style={{ height: "150px", objectFit: "cover" }}
                              />
                            )}
                            <div className="card-body">
                              <h6 className="card-title">{pub.place_name}</h6>
                              <p className="card-text small text-muted mb-2">
                                📍 {pub.address}
                              </p>
                              <p className="card-text small mb-2">
                                🌎 {pub.city}, {pub.province}, {pub.country}
                              </p>
                              {pub.rating_avg && pub.rating_avg > 0 && (
                                <p className="card-text small mb-2">
                                  ⭐ {pub.rating_avg.toFixed(1)} (
                                  {pub.rating_count || 0} reseñas)
                                </p>
                              )}
                              <DurationBadge durationMin={pub.duration_min} />
                              {pub.categories && pub.categories.length > 0 && (
                                <div className="mb-2">
                                  {pub.categories.map((cat, idx) => (
                                    <span
                                      key={idx}
                                      className="badge bg-secondary me-1"
                                    >
                                      {typeof cat === "string"
                                        ? cat
                                        : cat.name || cat.slug}
                                    </span>
                                  ))}
                                </div>
                              )}
                              {pub.cost_per_day && (
                                <div className="mb-2">
                                  <span className="badge bg-success">
                                    💰 ${pub.cost_per_day} por día
                                  </span>
                                </div>
                              )}
                              <PublicationAvailability publication={pub} />
                            </div>
                            <div className="card-footer">
                              <div className="d-grid gap-2">
                                <button
                                  className="btn btn-outline-info btn-sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    showPublicationDetail(pub);
                                  }}
                                >
                                  🔍 Ver detalle
                                </button>
                                <button
                                  className="btn btn-primary btn-sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    console.log(
                                      "🎯 [DEBUG] Publicación seleccionada para agregar:",
                                      pub.place_name,
                                    );
                                    addPublicationToSlot(pub);
                                  }}
                                >
                                  ➕ Agregar actividad
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="modal-footer">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => {
                      setShowPublicationModal(false);
                      setSelectedSlot(null);
                    }}
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  console.log("\u26a0\ufe0f [RENDER] FALLBACK - Ninguna condición cumplida");
  console.log(
    "\u26a0\ufe0f [RENDER] Step:",
    step,
    "ItineraryData existe:",
    !!itineraryData,
  );

  return (
    <div className="container mt-4">
      <div className="row justify-content-center">
        <div className="col-lg-6">
          <div className="alert alert-warning">
            <h5>\u26a0\ufe0f Estado inconsistente</h5>
            <p>
              <strong>Step:</strong> {step}
            </p>
            <p>
              <strong>ItineraryData:</strong>{" "}
              {itineraryData ? "Presente" : "Ausente"}
            </p>
            <p>
              <strong>Loading:</strong> {loading ? "Sí" : "No"}
            </p>
            <button
              className="btn btn-outline-custom mt-2"
              onClick={() => {
                console.log("\ud83d\udd04 Reseteando al step setup");
                setStep("setup");
                setItineraryData(null);
                setError("");
              }}
            >
              \ud83c\udfe0 Volver al inicio
            </button>
          </div>
        </div>
      </div>

      {showErrorModal && (
        <div
          className="modal show d-block"
          tabIndex="-1"
          style={{ backgroundColor: "rgba(0,0,0,0.5)" }}
        >
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header bg-danger text-white">
                <h5 className="modal-title">❌ Error al Agregar Actividad</h5>
                <button
                  type="button"
                  className="btn-close btn-close-white"
                  onClick={() => setShowErrorModal(false)}
                ></button>
              </div>
              <div className="modal-body">
                <div
                  style={{
                    whiteSpace: "pre-line",
                    fontFamily: "monospace",
                    fontSize: "14px",
                  }}
                >
                  {errorMessage}
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-danger"
                  onClick={() => setShowErrorModal(false)}
                >
                  Entendido
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
