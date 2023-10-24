import http from "k6/http";
import { check, sleep } from "k6";

export default function () {
    const res = http.get("https://comment-detector.org/ipaddress/49.217.49.133?target_collection=gossip");
    check(res, { 'status was 200': (r) => r.status === 200 });
    // sleep(1);
}

export const options = {
    vus: 1000,
    duration: '30s',
};

// export const options = {
//     stages: [
//         { duration: '30s', target: 1000 },
//         { duration: '1m30s', target: 2000 },
//         { duration: '20s', target: 0 },
//     ],
// };