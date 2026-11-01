import { createTheme, Button, Input, Select, Modal } from '@mantine/core';
export const tokens = {
  canvas: '#F4F9FB',
  studentCanvas: '#EDF6FA',
  studentHeader: '#E4F1F8',
  studentHover: '#D9EEF9',
  surface: '#FFFFFF',
  ink: '#193E51',
  muted: '#55717F',
  primary: '#0875B4',
  lesson: '#C8EBFC',
  mint: '#C8F0DB',
  materialInsetSurface: '#BDEBD2',
  reviewCheckedHover: '#B9E8CE',
  reviewSurface: '#FFF7DB',
  reviewActionSurface: '#FFE7A3',
  reviewActionHover: '#FFDC80',
  reviewActionActive: '#F5D071',
  reviewActionBorder: '#B18A30',
  materialMissingSurface: '#FFF2F0',
  materialMissingBadge: '#FFD8D2',
  success: '#276C4C',
  successSurface: '#E6F4EC',
  border: '#DBE7EE',
  controlBorder: '#7A929E',
  danger: '#B42318',
} as const;
export const theme = createTheme({
  black: tokens.ink,
  fontFamily: 'Manrope Variable, Manrope, system-ui, sans-serif',
  primaryColor: 'lgg',
  primaryShade: 6,
  colors: {
    lgg: [
      '#edf8fd',
      '#d9f0fc',
      '#bce4f8',
      '#91d2f3',
      '#5ebbe9',
      '#2b9ed8',
      tokens.primary,
      '#06659b',
      '#075680',
      '#084769',
    ],
  },
  fontSizes: {
    xs: '0.875rem',
    sm: '0.875rem',
    md: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
  },
  headings: {
    fontFamily: 'Manrope Variable, Manrope, system-ui, sans-serif',
    fontWeight: '750',
    sizes: {
      h1: { fontSize: '2.5rem', lineHeight: '1.15' },
      h2: { fontSize: '1.5rem', lineHeight: '1.3' },
    },
  },
  defaultRadius: 'md',
  radius: { sm: '0.375rem', md: '0.5rem', lg: '1rem' },
  components: {
    Button: Button.extend({
      defaultProps: { size: 'md' },
      styles: { root: { minHeight: 44 } },
    }),
    Input: Input.extend({ styles: { input: { minHeight: 44 } } }),
    Select: Select.extend({
      styles: {
        dropdown: { borderColor: tokens.controlBorder, borderRadius: 8 },
        option: { minHeight: 44, whiteSpace: 'normal' },
      },
    }),
    Modal: Modal.extend({
      defaultProps: {
        centered: true,
        attributes: { header: { role: 'presentation' } },
        overlayProps: { backgroundOpacity: 0.35 },
        returnFocus: true,
        trapFocus: true,
      },
    }),
  },
});
export const cssVariables = Object.fromEntries(
  Object.entries(tokens).map(([key, value]) => [`--lgg-${key}`, value]),
);
