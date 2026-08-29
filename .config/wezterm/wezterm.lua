local wezterm = require 'wezterm'

local config = {
  colors = {
    foreground = '#d8d8d8',
    background = '#181818',
    ansi = {
      '#181818', '#ac4242', '#90a959', '#f4bf75',
      '#6a9fb5', '#aa759f', '#75b5aa', '#d8d8d8',
    },
    brights = {
      '#6b6b6b', '#c55555', '#aac474', '#feca88',
      '#82b8c8', '#c28cb8', '#93d3c3', '#f8f8f8',
    },
  },

  enable_tab_bar = false,
  window_decorations = 'NONE',
  window_padding = {
    left = 0,
    right = 0,
    top = 0,
    bottom = 0,
  },

  disable_default_key_bindings = true,
  keys = {
    { key = 'n', mods = 'CTRL|SHIFT', action = wezterm.action.SpawnWindow },
    { key = '-', mods = 'CTRL', action = wezterm.action.DecreaseFontSize },
    { key = '=', mods = 'CTRL', action = wezterm.action.IncreaseFontSize },
  },
}

return config
