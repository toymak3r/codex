// Common store functions
import { defineStore } from "pinia";

import API from "@/api/v3/common";
import _ from "lodash";

const getErrors = (axiosError) => {
  let errors = [];
  if (axiosError && axiosError.response && axiosError.response.data) {
    const data = axiosError.response.data;
    errors = _.flatten(data);
  } else {
    console.warn("Unable to parse error", axiosError);
  }
  if (errors.length === 0) {
    errors = ["Unknown error"];
  }
  return errors;
};

export const useCommonStore = defineStore("common", {
  state: () => ({
    form: {
      errors: [],
      success: "",
    },
    versions: {
      // This is injected by vite define
      installed: CODEX_PACKAGE_VERSION, // eslint-disable-line no-undef
      latest: undefined,
    },
    timestamp: Date.now(),
  }),
  actions: {
    async loadVersions() {
      await API.getVersions(this.timestamp)
        .then((response) => {
          const data = response.data;
          return (this.versions = data);
        })
        .catch(console.error);
    },
    downloadIOSPWAFix(href, fileName) {
      API.downloadIOSPWAFix(href, fileName);
    },
    setErrors(axiosError) {
      this.$patch((state) => {
        state.form.errors = getErrors(axiosError);
        state.form.success = "";
      });
    },
    setSuccess(success) {
      this.$patch((state) => {
        state.form.errors = [];
        state.form.success = success;
      });
    },
    clearErrors() {
      this.$patch((state) => {
        state.form.errors = [];
        state.form.success = "";
      });
    },
  },
});
