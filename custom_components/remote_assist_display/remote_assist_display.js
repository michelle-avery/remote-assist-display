class StyleManager {
  getStyleElement(root, prefix) {
    if (!root) return null;
    return root.querySelector(`#${prefix}`);
  }

  createStyleSheet(css, prefix) {
    const style = document.createElement('style');
    style.setAttribute('id', prefix);
    style.innerHTML = css;
    return style;
  }

  addStyle(css, root, prefix) {
    if (!root) return;

    let styleElement = this.getStyleElement(root, prefix);
    if (!styleElement) {
      styleElement = this.createStyleSheet(css, prefix);
      root.appendChild(styleElement);
    } else {
      styleElement.innerHTML = css;
    }
  }

  removeStyle(root, prefix) {
    if (!root) return;
    const styleElement = this.getStyleElement(root, prefix);
    if (styleElement) {
      styleElement.remove();
    }
  }
}

const STYLES = {
  HEADER: {
    '#view': {
      'min-height': '100vh !important',
      '--header-height': '0px !important',
      '--kiosk-header-height': '0px !important',
      'padding-top': 'calc(var(--kiosk-header-height) + env(safe-area-inset-top)) !important'
    },
    '.header': {
      'display': 'none !important'
    },
    'app-header': {
      'display': 'none !important'
    },
    'ha-app-layout': {
      '--header-height': '0px !important'
    },
    'div[action-items]': {
      'display': 'none !important'
    },
    'header > .toolbar': {
      'display': 'none !important'
    }
  },
  SIDEBAR: {
    ':host': {
      '--mdc-drawer-width': '0px !important'
    },
    'partial-panel-resolver': {
      '--mdc-top-app-bar-width': '100% !important'
    },
    'ha-drawer > ha-sidebar': {
      'display': 'none !important'
    },
    'ha-menu-button': {
      'display': 'none !important'
    },
    '.mdc-drawer': {
      'display': 'none !important'
    }
  }
};


function convertStylesToCSS(styles) {
  return Object.entries(styles)
    .map(([selector, rules]) => {
      const cssRules = Object.entries(rules)
        .map(([property, value]) => `${property}: ${value}`)
        .join(';');
      return `${selector} { ${cssRules} }`;
    })
    .join('\n');
}

class RemoteAssistDisplay {
  constructor() {
    console.log("RemoteAssistDisplay initializing");
    this.styleManager = new StyleManager();
    this.initAttempts = 0;
    this.initializeWhenReady();
  }

  async initializeWhenReady(attempts = 0) {
    if (attempts > 50) {
      console.log("Failed to initialize after 50 attempts");
      return;
    }

    try {
      const ha = document.querySelector("home-assistant");
      if (!ha?.shadowRoot || !ha.hass) {
        throw new Error("Home Assistant not ready");
      }

      const main = ha.shadowRoot.querySelector("home-assistant-main");
      if (!main?.shadowRoot) {
        throw new Error("Main UI not ready");
      }

      this.ha = ha;
      this.main = main.shadowRoot;
      console.log("RemoteAssistDisplay initialized");

      await this.waitForElement(
        () => this.main.querySelector("partial-panel-resolver"),
        "panel resolver"
      );

      this.setupObservers();
      await this.checkForLovelacePanel();

    } catch (e) {
      console.log("Initialization retry:", e.message);
      setTimeout(() => this.initializeWhenReady(attempts + 1), 100);
    }
  }

  setupObservers() {
    const resolver = this.main.querySelector("partial-panel-resolver");
    if (resolver) {
      console.log("Setting up panel observer");
      new MutationObserver((mutations) => {
        for (const mutation of mutations) {
          for (const node of mutation.addedNodes) {
            if (node.localName === "ha-panel-lovelace") {
              console.log("Lovelace panel detected");
              setTimeout(() => this.run(node), 100);
            }
          }
        }
      }).observe(resolver, { childList: true });
    }

    window.addEventListener("location-changed", () => {
      console.log("Location changed, checking for panel");
      this.checkForLovelacePanel();
    });
  }

  async checkForLovelacePanel() {
    const resolver = this.main.querySelector("partial-panel-resolver");
    if (!resolver) return;

    const panel = resolver.querySelector("ha-panel-lovelace");
    if (panel) {
      console.log("Found existing lovelace panel");
      await this.run(panel);
    } else {
      console.log("No lovelace panel currently present");
    }
  }

  async run(lovelacePanel) {
    if (!lovelacePanel) {
      console.log("No panel provided to run");
      return;
    }

    const displayId = localStorage.getItem("remote_assist_display_id");
    if (!displayId) return;

    const settings = JSON.parse(localStorage.getItem(`remote_assist_display_settings`) || "{}");
    if (!settings.hideHeader && !settings.hideSidebar) return;

    console.log("Applying display settings:", settings);

    try {
      await this.waitForElement(() => lovelacePanel.lovelace?.config, "panel config");
      const huiRoot = lovelacePanel.shadowRoot?.querySelector("hui-root");
      await this.waitForElement(() => huiRoot?.shadowRoot, "hui-root shadow");

      if (settings.hideHeader) {
        console.log("Applying header styles");
        const css = convertStylesToCSS(STYLES.HEADER);
        this.styleManager.addStyle(css, huiRoot.shadowRoot, 'remote-assist-display-header');
      }

      if (settings.hideSidebar) {
        console.log("Applying sidebar styles");
        const css = convertStylesToCSS(STYLES.SIDEBAR);
        this.styleManager.addStyle(css, this.main, 'remote-assist-display-sidebar');
      }

      // Refresh view
      window.dispatchEvent(new Event("resize"));
    } catch (e) {
      console.log("Configuration error:", e.message);
    }
  }

  async waitForElement(getter, name, maxAttempts = 100) {
    for (let i = 0; i < maxAttempts; i++) {
      const result = getter();
      if (result) {
        console.log(`Found ${name}`);
        return result;
      }
      await new Promise(r => setTimeout(r, 50));
    }
    throw new Error(`Timeout waiting for ${name}`);
  }
}

// Initialize when core web components are ready
Promise.all([
  customElements.whenDefined("home-assistant"),
  customElements.whenDefined("hui-view")
]).then(() => {
  console.log("Starting RemoteAssistDisplay");
  window.RemoteAssistDisplay = new RemoteAssistDisplay();
});