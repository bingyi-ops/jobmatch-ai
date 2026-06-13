/**
 * 用户身份标识工具
 * 首次访问时自动生成 UUID，存入 localStorage，后续请求自动携带
 * 无需登录注册，但换浏览器/清除 localStorage 后身份会丢失
 */
const STORAGE_KEY = 'jobmatch_user_key';

export function getUserKey(): string {
  let key = localStorage.getItem(STORAGE_KEY);
  if (!key) {
    key = crypto.randomUUID();
    localStorage.setItem(STORAGE_KEY, key);
  }
  return key;
}

export function resetUserKey(): void {
  localStorage.removeItem(STORAGE_KEY);
}

export function getUserKeyDisplay(): string {
  return getUserKey().slice(0, 8) + '...';
}
