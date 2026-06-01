export const colors = {
  black: '#271410',
  dark: '#603A2C',
  mid: '#8B6B5A',
  light: '#B8A094',
  border: '#D4C8C0',
  borderLight: '#E8E0D8',
  bg: '#F5F0EC',
  bgHover: '#EBE3DC',
  white: '#fff',
}

export const badge = (status) => ({
  display: 'inline-block',
  padding: '2px 8px',
  borderRadius: 3,
  fontSize: 11,
  fontWeight: 500,
  background:
    status === 'hired' ? colors.black :
    status === 'rejected' ? colors.bg :
    status === 'reviewed' ? colors.bgHover :
    colors.bg,
  color:
    status === 'hired' ? colors.white :
    status === 'rejected' ? colors.black :
    status === 'reviewed' ? colors.dark :
    colors.mid,
  border: status === 'rejected' ? `1px solid ${colors.border}` : 'none',
})

export const scoreBadge = (score) => ({
  padding: '1px 6px',
  borderRadius: 3,
  fontSize: 12,
  fontWeight: 500,
  background:
    score >= 5 ? colors.black :
    score >= 4 ? colors.dark :
    score >= 3 ? colors.mid :
    score >= 2 ? colors.light :
    colors.border,
  color:
    score >= 3 ? colors.white : colors.dark,
})

export const card = {
  background: colors.white,
  border: `1px solid ${colors.borderLight}`,
  borderRadius: 8,
  padding: 20,
  marginBottom: 16,
}

export const input = {
  width: '100%',
  padding: '8px 10px',
  border: `1px solid ${colors.border}`,
  borderRadius: 4,
  fontSize: 13,
  outline: 'none',
  boxSizing: 'border-box',
}

export const select = {
  ...input,
  background: colors.white,
}

export const label = {
  display: 'block',
  fontSize: 11,
  fontWeight: 600,
  color: colors.mid,
  marginBottom: 4,
  textTransform: 'uppercase',
  letterSpacing: '0.3px',
}

export const btn = (bg = colors.black) => ({
  padding: '8px 16px',
  border: 'none',
  borderRadius: 4,
  background: bg,
  color: colors.white,
  fontSize: 12,
  fontWeight: 500,
  cursor: 'pointer',
})

export const btnOutline = {
  padding: '7px 14px',
  border: `1px solid ${colors.border}`,
  borderRadius: 4,
  background: colors.white,
  cursor: 'pointer',
  fontSize: 12,
  color: colors.dark,
  transition: 'background 0.15s, border-color 0.15s',
}

export const th = {
  textAlign: 'left',
  padding: '10px 24px',
  borderBottom: `1px solid ${colors.borderLight}`,
  fontSize: 11,
  fontWeight: 600,
  color: colors.mid,
  textTransform: 'uppercase',
  letterSpacing: '0.4px',
  background: colors.bg,
}

export const td = {
  padding: '10px 24px',
  borderBottom: `1px solid ${colors.borderLight}`,
  fontSize: 13,
}

export const paginationBtn = (disabled) => ({
  padding: '6px 14px',
  border: `1px solid ${colors.border}`,
  borderRadius: 4,
  background: disabled ? colors.bg : colors.white,
  cursor: disabled ? 'not-allowed' : 'pointer',
  fontSize: 12,
  color: disabled ? colors.border : colors.dark,
})
