# Estructura Modular del Frontend

## 📁 Nueva Organización

```
frontend/src/
├── components/
│   ├── shared/              # Componentes reutilizables
│   │   ├── UIComponents.jsx         # Stars, Badges, Alerts, EmptyState
│   │   ├── PhotoCarousel.jsx        # Carrusel de fotos
│   │   ├── PublicationCard.jsx      # Tarjeta de publicación
│   │   ├── PublicationsGrid.jsx     # Grid de publicaciones
│   │   ├── MultiCategoryDropdown.jsx # Dropdown de categorías
│   │   └── StatsSidebar.jsx         # Sidebar de estadísticas
│   ├── AuthForm.jsx
│   ├── CreatePublicationForm.jsx
│   ├── ItineraryRequestForm.jsx
│   ├── Navbar.jsx
│   └── Sidebar.jsx
├── hooks/
│   └── useOnClickOutside.js # Hook para detectar clicks fuera
├── pages/
│   ├── Home.jsx
│   ├── Backoffice.jsx
│   └── ...
└── utils/
    └── api.js               # request() y useToken()
```

## 🔧 Componentes Reutilizables Creados

### 1. **UIComponents.jsx**
Componentes básicos de interfaz:
- `Stars({ value })` - Estrellas de rating
- `RatingBadge({ avg, count })` - Badge con rating
- `StatusBadge({ status })` - Badge de estado (approved/pending/rejected/deleted)
- `LoadingSpinner({ message })` - Indicador de carga
- `ErrorAlert({ message, onDismiss })` - Alerta de error
- `SuccessAlert({ message, onDismiss })` - Alerta de éxito
- `EmptyState({ message, icon })` - Estado vacío

### 2. **PhotoCarousel.jsx**
Carrusel de fotos reutilizable con:
- Múltiples fotos con navegación
- Indicadores y controles
- Altura configurable
- Prefijo de ID personalizable

**Props:**
```jsx
<PhotoCarousel 
  photos={[]} 
  publicationId={id} 
  height={260}
  carouselPrefix="carousel"
/>
```

### 3. **PublicationCard.jsx**
Tarjeta de publicación completa y configurable:
- Muestra fotos, título, ubicación
- Status badges opcionales
- Rating opcional
- Botón de favorito opcional
- Menú de acciones customizable
- Footer customizable

**Props:**
```jsx
<PublicationCard
  publication={pub}
  carouselPrefix="carousel"
  showStatus={true}
  showRating={true}
  showFavorite={true}
  isFavorite={false}
  onToggleFavorite={handleToggle}
  actions={<ActionMenu />}
  footer={<CustomFooter />}
  showDetails={true}
/>
```

### 4. **PublicationsGrid.jsx**
Grid completo para listar publicaciones:
- Manejo de loading
- Manejo de estado vacío
- Grid responsive (1/2/3 columnas)
- Integra PublicationCard

**Props:**
```jsx
<PublicationsGrid
  publications={pubs}
  loading={false}
  emptyMessage="No hay publicaciones"
  carouselPrefix="grid"
  showStatus={true}
  showRating={true}
  showFavorite={true}
  favorites={[1, 2, 3]}
  onToggleFavorite={handleToggle}
  renderActions={(pub) => <Actions pub={pub} />}
  renderFooter={(pub) => <Footer pub={pub} />}
  showDetails={true}
/>
```

### 5. **MultiCategoryDropdown.jsx**
Dropdown multiselect para filtrar categorías:
- Checkboxes múltiples
- Botón de limpiar
- Recarga de categorías
- Click fuera para cerrar

**Props:**
```jsx
<MultiCategoryDropdown
  allCats={categories}
  selected={selectedCats}
  onApply={handleApply}
  onReload={handleReload}
/>
```

### 6. **StatsSidebar.jsx**
Sidebar con estadísticas:
- Tarjetas de estadísticas
- Iconos y colores personalizables
- Sticky positioning

**Props:**
```jsx
<StatsSidebar 
  stats={[
    { icon: "📝", label: "Publicaciones", value: 10, color: "primary" },
    { icon: "⏳", label: "Pendientes", value: 5, color: "warning" }
  ]}
/>
```

## 🔨 Utilidades

### **api.js**
```javascript
import { request, useToken } from '../utils/api';

// Hacer peticiones
const data = await request('/api/endpoint', { 
  method: 'POST', 
  token, 
  body: { key: 'value' } 
});

// Obtener token
const token = useToken();
```

### **useOnClickOutside.js**
```javascript
import { useOnClickOutside } from '../hooks/useOnClickOutside';

const ref = useRef();
useOnClickOutside(ref, () => setOpen(false));
```

## 🎯 Beneficios

1. **Código DRY**: Eliminación de código duplicado entre Home.jsx y Backoffice.jsx
2. **Mantenibilidad**: Cambios en un solo lugar afectan todo el proyecto
3. **Consistencia**: UI uniforme en toda la aplicación
4. **Testabilidad**: Componentes aislados más fáciles de testear
5. **Reutilización**: Componentes listos para usar en nuevas features
6. **Escalabilidad**: Fácil agregar nuevas funcionalidades

## 📝 Próximos Pasos para Refactorizar

### Home.jsx
- Reemplazar código duplicado con componentes compartidos
- Usar `PublicationsGrid` en lugar de código repetitivo
- Importar utilidades de `utils/api.js`
- Usar `StatusBadge` y otros componentes de UI

### Backoffice.jsx
- Aplicar los mismos cambios que Home.jsx
- Usar `StatsSidebar` para las estadísticas
- Simplificar vistas con componentes modulares

## 🔄 Ejemplo de Migración

### Antes:
```jsx
{pubs.map((p) => (
  <div className="col" key={p.id}>
    <div className="card">
      {/* 50+ líneas de código repetido */}
    </div>
  </div>
))}
```

### Después:
```jsx
<PublicationsGrid
  publications={pubs}
  showRating={true}
  showFavorite={true}
  onToggleFavorite={handleToggle}
/>
```

**Reducción: ~80% menos código por vista** 🎉
