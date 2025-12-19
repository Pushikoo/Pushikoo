/**
 * plugins/vuetify.ts
 *
 * Modern Material Design 3 inspired theme configuration - Blue Theme
 */

// Styles
import "@mdi/font/css/materialdesignicons.css";
import "vuetify/styles";

// Composables
import { createVuetify } from "vuetify";

// Modern color palette - Blue accent theme
const lightTheme = {
  dark: false,
  colors: {
    background: "#FAFBFC",
    surface: "#FFFFFF",
    "surface-bright": "#FFFFFF",
    "surface-light": "#F5F7FA",
    "surface-variant": "#E3F2FD",
    "on-surface-variant": "#1565C0",
    primary: "#1976D2",
    "primary-darken-1": "#1565C0",
    secondary: "#26A69A",
    "secondary-darken-1": "#00897B",
    tertiary: "#7C4DFF",
    error: "#D32F2F",
    info: "#0288D1",
    success: "#388E3C",
    warning: "#F57C00",
    "on-background": "#1C1B1F",
    "on-surface": "#1C1B1F",
    "on-primary": "#FFFFFF",
    "on-secondary": "#FFFFFF",
    "on-error": "#FFFFFF",
    "on-info": "#FFFFFF",
    "on-success": "#FFFFFF",
    "on-warning": "#FFFFFF",
  },
  variables: {
    "border-color": "#E0E0E0",
    "border-opacity": 0.12,
    "high-emphasis-opacity": 0.87,
    "medium-emphasis-opacity": 0.6,
    "disabled-opacity": 0.38,
    "idle-opacity": 0.04,
    "hover-opacity": 0.08,
    "focus-opacity": 0.12,
    "selected-opacity": 0.08,
    "activated-opacity": 0.12,
    "pressed-opacity": 0.12,
    "dragged-opacity": 0.08,
    "theme-kbd": "#212529",
    "theme-on-kbd": "#FFFFFF",
    "theme-code": "#F5F5F5",
    "theme-on-code": "#000000",
  },
};

const darkTheme = {
  dark: true,
  colors: {
    background: "#121212",
    surface: "#1E1E1E",
    "surface-bright": "#2D2D2D",
    "surface-light": "#262626",
    "surface-variant": "#1E3A5F",
    "on-surface-variant": "#90CAF9",
    primary: "#64B5F6",
    "primary-darken-1": "#42A5F5",
    secondary: "#4DB6AC",
    "secondary-darken-1": "#26A69A",
    tertiary: "#B388FF",
    error: "#EF5350",
    info: "#29B6F6",
    success: "#66BB6A",
    warning: "#FFA726",
    "on-background": "#E6E1E5",
    "on-surface": "#E6E1E5",
    "on-primary": "#0D47A1",
    "on-secondary": "#003731",
    "on-error": "#601410",
    "on-info": "#003549",
    "on-success": "#1B5E20",
    "on-warning": "#E65100",
  },
  variables: {
    "border-color": "#FFFFFF",
    "border-opacity": 0.12,
    "high-emphasis-opacity": 0.87,
    "medium-emphasis-opacity": 0.6,
    "disabled-opacity": 0.38,
    "idle-opacity": 0.1,
    "hover-opacity": 0.08,
    "focus-opacity": 0.12,
    "selected-opacity": 0.16,
    "activated-opacity": 0.24,
    "pressed-opacity": 0.16,
    "dragged-opacity": 0.08,
    "theme-kbd": "#212529",
    "theme-on-kbd": "#FFFFFF",
    "theme-code": "#343434",
    "theme-on-code": "#CCCCCC",
  },
};

export default createVuetify({
  theme: {
    defaultTheme: "light",
    themes: {
      light: lightTheme,
      dark: darkTheme,
    },
  },
  defaults: {
    VBtn: {
      rounded: "lg",
      fontWeight: 500,
    },
    VCard: {
      rounded: "lg",
      elevation: 0,
      border: true,
    },
    VTextField: {
      variant: "outlined",
      density: "comfortable",
      color: "primary",
    },
    VSelect: {
      variant: "outlined",
      density: "comfortable",
      color: "primary",
    },
    VAutocomplete: {
      variant: "outlined",
      density: "comfortable",
      color: "primary",
    },
    VTextarea: {
      variant: "outlined",
      density: "comfortable",
      color: "primary",
    },
    VFileInput: {
      variant: "outlined",
      density: "comfortable",
      color: "primary",
    },
    VCheckbox: {
      color: "primary",
    },
    VSwitch: {
      color: "primary",
      inset: true,
    },
    VChip: {
      rounded: "lg",
    },
    VList: {
      rounded: "lg",
    },
    VDialog: {
      VCard: {
        rounded: "xl",
      },
    },
    VDataTable: {
      hover: true,
    },
    VDataTableServer: {
      hover: true,
    },
    VAppBar: {
      elevation: 0,
      border: true,
    },
    VNavigationDrawer: {
      elevation: 0,
    },
    VToolbar: {
      color: "surface",
    },
    VAlert: {
      rounded: "lg",
      variant: "tonal",
    },
    VSnackbar: {
      rounded: "lg",
    },
  },
});
