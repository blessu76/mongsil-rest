// 기존 한국어 루트에서 ?lang=을 처리한다. 저장 언어와 브라우저 감지는 웹킷이 맡는다.
(() => {
  const picker = document.getElementById("ipe-lang-select");
  const current = picker?.selectedOptions[0];
  if (!current || current.lang !== "ko") return;

  const url = new URL(location.href);
  const requested = url.searchParams.get("lang")?.trim().toLowerCase();
  if (!requested) return;

  const edition = Array.from(picker.options).find((option) => option.lang.toLowerCase() === requested);
  if (!edition) return;

  try {
    localStorage.setItem("ipe_lang", edition.lang);
  } catch {
    // 저장소 접근이 차단되어도 이번 방문의 언어는 바꾼다.
  }
  url.searchParams.delete("lang");
  document.querySelector("script[data-redirect]")?.removeAttribute("data-redirect");
  if (edition.value === current.value) {
    history.replaceState(null, "", url);
  } else {
    url.pathname = edition.value;
    location.replace(url);
  }
})();
