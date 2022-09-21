import { HTTP } from "./base";

const downloadIOSPWAFix = (href, fileName) => {
  // iOS has a download bug inside PWAs. The user is trapped in the
  // download screen and cannot return to the app.
  // https://developer.apple.com/forums/thread/95911
  // This works around that by creating temporary blob link which
  // makes the PWA display browser back controls
  HTTP.get(href, { responseType: "blob" })
    .then((response) => {
      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(response.data);
      link.download = fileName;
      link.click();
      return true;
    })
    .catch((error) => console.warn(error));
};

const getVersions = () => {
  return HTTP.get("/version");
};

export default {
  downloadIOSPWAFix,
  getVersions,
};
