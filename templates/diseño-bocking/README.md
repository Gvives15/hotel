# Diseño Booking-Like - Sistema de Plantillas

## 📋 Descripción General

Este sistema de plantillas proporciona una experiencia de usuario moderna y profesional inspirada en Booking.com, diseñada específicamente para hoteles que desean ofrecer una interfaz de reservas premium a sus clientes.

## 🎨 Sistema de Diseño

### Paleta de Colores

```css
/* Colores principales */
--clr-primary: #003580;        /* Azul Booking principal */
--clr-primary-light: #0071c2;  /* Azul claro para hover */
--clr-accent: #febb02;         /* Amarillo para highlights */
--clr-success: #008009;        /* Verde para estados positivos */
--clr-error: #d4111e;          /* Rojo para errores */

/* Colores neutrales */
--clr-bg: #f5f5f5;             /* Fondo principal */
--clr-bg-card: #ffffff;        /* Fondo de tarjetas */
--clr-border: #e6e6e6;         /* Bordes */
--clr-text: #262626;           /* Texto principal */
--clr-text-light: #6b6b6b;    /* Texto secundario */
--clr-white: #ffffff;          /* Blanco */
```

### Tipografía

- **Fuente principal**: Inter (Google Fonts)
- **Pesos disponibles**: 400, 500, 600, 700, 800
- **Tamaños**: Desde 12px hasta 36px
- **Altura de línea**: 1.5 para óptima legibilidad

### Sistema de Espaciado

Basado en un sistema de 4px con multiplicadores:
```css
--space-1: 0.25rem;  /* 4px */
--space-2: 0.5rem;   /* 8px */
--space-3: 0.75rem;  /* 12px */
--space-4: 1rem;     /* 16px */
--space-6: 1.5rem;   /* 24px */
--space-8: 2rem;     /* 32px */
--space-12: 3rem;    /* 48px */
--space-16: 4rem;    /* 64px */
```

## 🧩 Componentes Disponibles

### Botones

```html
<!-- Botón primario -->
<button class="btn btn--primary btn--lg">Reservar ahora</button>

<!-- Botón con ícono -->
<button class="btn btn--accent btn--md">
  <i class="fas fa-search"></i>
  <span>Buscar</span>
</button>

<!-- Botón outline -->
<a href="#" class="btn btn--outline btn--sm">Ver detalles</a>
```

### Tarjetas

```html
<article class="card">
  <div class="card__media">
    <img src="imagen.jpg" alt="Descripción">
  </div>
  <div class="card__body">
    <h3 class="card__title">Título de la tarjeta</h3>
    <p class="card__meta">Metadatos</p>
    <div class="card__actions">
      <button class="btn btn--primary">Acción</button>
    </div>
  </div>
</article>
```

### Formularios

```html
<div class="field">
  <label for="input">Label</label>
  <input id="input" type="text" class="input" placeholder="Placeholder">
</div>
```

### Badges

```html
<span class="badge badge--success">Disponible</span>
<span class="badge badge--premium">Más Popular</span>
<span class="badge badge--neutral">Información</span>
```

## 🎯 Animaciones y Transiciones

### Animaciones Disponibles

- `animate-fadeIn`: Entrada suave de abajo
- `animate-fadeInUp`: Entrada desde abajo con desfase
- `animate-fadeInLeft`: Entrada desde la izquierda
- `animate-fadeInRight`: Entrada desde la derecha
- `animate-scaleIn`: Entrada con escala
- `animate-pulse`: Pulso continuo

### Transiciones

```css
--transition-fast: 150ms ease;
--transition: 250ms ease;
--transition-slow: 350ms ease;
```

## 📱 Diseño Responsivo

### Breakpoints

- **Móvil**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

### Características Responsivas

1. **Menú móvil**: Hamburger menu con animaciones suaves
2. **Grid adaptable**: Sistema de columnas que se ajusta al viewport
3. **Tipografía fluida**: Tamaños de fuente que escalan proporcionalmente
4. **Espaciado dinámico**: Espaciado que se ajusta al tamaño de pantalla

## 🚀 Características Especiales

### Hero Section
- Background gradient con overlay
- Animaciones escalonadas
- Estadísticas con íconos
- Formulario de búsqueda integrado

### Room Cards
- Hover effects con transformaciones
- Badges dinámicos
- Precios con descuentos mostrados
- Vista rápida al hacer hover

### Trust Indicators
- Estadísticas de satisfacción
- Certificaciones visibles
- Reseñas y calificaciones
- Seguridad de pago destacada

## 🔧 Implementación

### 1. Configuración del Hotel

Para usar este diseño, el hotel debe tener:
```python
hotel.template_id = 'nuevo'  # Esto activará el diseño booking-like
```

### 2. Estructura de Templates

```
templates/
└── diseño-bocking/
    ├── base.html          # Template base con header/footer
    ├── home.html          # Página principal
    └── README.md          # Esta documentación
```

### 3. Archivos Estáticos

```
static/
└── diseño-bocking/
    └── styles.css         # Todos los estilos del sistema
```

## 🎨 Personalización

### Colores
Modifica las variables CSS en `:root` para cambiar la paleta de colores.

### Tipografía
Actualiza la fuente en la importación de Google Fonts y ajusta los pesos disponibles.

### Componentes
Todos los componentes están diseñados para ser fácilmente personalizables mediante clases CSS.

## 📊 Rendimiento

- **CSS optimizado**: Un solo archivo con todos los estilos
- **Animaciones eficientes**: Usan transform y opacity para mejor rendimiento
- **Imágenes responsivas**: Optimizadas para diferentes dispositivos
- **Lazy loading**: Implementado para imágenes y contenido

## ♿ Accesibilidad

- **ARIA labels**: Implementados en elementos interactivos
- **Contraste de colores**: Cumple con estándares WCAG 2.1
- **Navegación por teclado**: Todos los elementos son navegables
- **Screen readers**: Estructura semántica apropiada

## 🌟 Mejores Prácticas

1. **Mobile-first**: Diseñado primero para móviles
2. **Progressive enhancement**: Funcionalidad básica primero
3. **Semantic HTML**: Uso apropiado de elementos HTML5
4. **BEM methodology**: Convención de nombres consistente
5. **Performance budget**: Optimizado para carga rápida

## 🔗 Recursos Adicionales

- [Google Fonts - Inter](https://fonts.google.com/specimen/Inter)
- [Font Awesome Icons](https://fontawesome.com/)
- [Booking.com Design System](https://booking.design/)

---

**Última actualización**: Noviembre 2025
**Versión**: 1.0.0
**Autor**: Sistema de Plantillas O11CE