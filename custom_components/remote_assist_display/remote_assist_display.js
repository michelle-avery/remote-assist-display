const RemoteAssistDisplay = (SuperClass) => {
  class RemoteAssistDisplayClass extends SuperClass {
    constructor() {
      super();
      this._setupDisplay();

      window.addEventListener("location-changed", () => {
        this._setupDisplay();
      });
    }

    async _setupDisplay() {
      // Get display settings from localStorage
      const displayId = localStorage.getItem("remote_assist_display_id");
      if (!displayId) return;  // Not a remote assist display instance

      const settings = JSON.parse(localStorage.getItem(`remote_assist_display_${displayId}_settings`) || "{}");

      if (settings.hideHeader || settings.hideSidebar) {
        await this._hideChrome(settings);
      }
    }

    async _hideChrome(settings) {
      const rootEl = await this._getRootElement();
      if (!rootEl) return;

      let header = await this._findHeader(rootEl);
      let menuButton;

      if (header) {
        menuButton = header.querySelector("ha-menu-button");
      } else {
        // Try alternative header location
        let el = rootEl;
        let steps = 0;
        while (el && el.localName !== "ha-top-app-bar-fixed" && steps++ < 5) {
          await this._waitForElement(el, true);
          const next = el.querySelector("ha-top-app-bar-fixed")
                      ?? el.firstElementChild
                      ?? el.shadowRoot;
          el = next;
        }

        if (el?.localName === "ha-top-app-bar-fixed") {
          header = el.shadowRoot.querySelector("header");
          menuButton = el.querySelector("ha-menu-button");
        }
      }

      if (!header && !menuButton) return;

      if (header && settings.hideHeader) {
        rootEl.style.setProperty("--header-height", "0px");
        header.style.setProperty("display", "none");
      }

      if (settings.hideSidebar) {
        if (menuButton) {
          menuButton.remove();
        }

        const mainEl = document.querySelector("home-assistant home-assistant-main");
        if (mainEl) {
          mainEl.style.setProperty("--mdc-drawer-width", "0px");
        }

        const sidebar = document.querySelector(
          "home-assistant home-assistant-main ha-drawer ha-sidebar"
        );
        if (sidebar) {
          sidebar.remove();
        }
      }
    }

    async _getRootElement() {
      const rootSelector = "home-assistant home-assistant-main ha-drawer partial-panel-resolver";
      const parts = rootSelector.split(" ");
      let current = document.body;

      for (const part of parts) {
        current = await this._findElement(part, current);
        if (!current) return null;
        if (current.shadowRoot) {
          current = current.shadowRoot;
        }
      }
      return current;
    }

    async _findElement(selector, root = document.body) {
      for (let i = 0; i < 10; i++) {
        const el = root.querySelector(selector);
        if (el) return el;
        await new Promise(r => setTimeout(r, 500));
      }
      return null;
    }

    async _findHeader(rootEl) {
      return await this._findElement(
        "ha-panel-lovelace hui-root .header",
        rootEl
      );
    }

    async _waitForElement(el, shadowRoot = false) {
      if (shadowRoot) {
        while (!el.shadowRoot) {
          await new Promise(r => setTimeout(r, 100));
        }
      }
      return true;
    }
  }

  return RemoteAssistDisplayClass;
};

// Only register if not already registered
const ELEMENT_NAME = "remote-assist-display";
if (!customElements.get(ELEMENT_NAME)) {
  const displayElement = RemoteAssistDisplay(HTMLElement);
  customElements.define(ELEMENT_NAME, displayElement);
}