(require '[com.sixsq.slipstream.clj-client.run :as ss-r])

(def metric-thold 7000.0)
(def node-name "webapp")
(def scale-up-by 2)

(def busy? (atom false))
(defn busy! [] (reset! busy? true))
(defn free! [] (reset! busy? false))

(let [index (default :ttl 20 (index))]
     (streams

       index

       (where (and (tagged "httpclient") (service #"^avg_response_time") (>= metric metric-thold))
              (if (and (not @busy?) (ss-r/can-scale?))
                (fn [& res]
                    (busy!)
                    (info "Starting scaling..." res)
                    (ss-r/action-scale-up node-name scale-up-by)
                    (info "Finished scaling..." res)
                    (free!))
                #(info "Busy scaling. Run state: " (ss-r/get-state) %)))

       (expired
         #(info "expired" %))))
