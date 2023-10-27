import http from "k6/http";
import { check, sleep } from "k6";

export default function () {
    const res = http.get("https://comment-detector.org");
    check(res, { 'status was 200': (r) => r.status === 200 });
    // sleep(1);
}

export const options = {
    vus: 5000,
    duration: '180s',
};

// export const options = {
//     stages: [
//         { duration: '30s', target: 1000 },
//         { duration: '1m30s', target: 2000 },
//         { duration: '20s', target: 0 },
//     ],
// };