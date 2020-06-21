package main

import (
	"context"
	"io/ioutil"
	"log"
	"net/http"
	"sync"

	"github.com/jackc/pgx/v4/pgxpool"
)

var pool *pgxpool.Pool

func showErr(w http.ResponseWriter, err error) {
	if err != nil {
		http.Error(w, err.Error(), 500)
	}
}

func insert(wg *sync.WaitGroup, w http.ResponseWriter, r *http.Request) {
	defer wg.Done()
	request, err := ioutil.ReadAll(r.Body)
	showErr(w, err)
	_, err = pool.Exec(r.Context(), "INSERT INTO demo (data) VALUES($1)", request)
	showErr(w, err)
}

func selects(wg *sync.WaitGroup, w http.ResponseWriter, r *http.Request) {
	defer wg.Done()
	var body string
	err := pool.QueryRow(r.Context(), "SELECT data::text FROM demo ORDER BY id DESC LIMIT 1").Scan(&body)
	showErr(w, err)
	w.Write([]byte(body))
}

func view(w http.ResponseWriter, r *http.Request) {
	var wg sync.WaitGroup
	wg.Add(2)
	go insert(&wg, w, r)
	go selects(&wg, w, r)
	wg.Wait()
}

func main() {
	var err error
	pool, err = pgxpool.Connect(context.Background(), "")
	if err != nil {
		log.Print(err)
	}
	defer pool.Close()
	http.HandleFunc("/", view)
	err = http.ListenAndServe(":80", nil)
	if err != nil {
		log.Print(err)
	}
}
