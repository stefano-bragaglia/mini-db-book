[🏠 Contents](index.md) · [← Previous: Appendix D — Answers to the Exercises](appendix-d-answers.md)

# References

Every work cited in the book, grouped by topic. Each entry links back to the chapters that cite it. Most of the papers are short and readable; the starred ones (★) are good first reads.

## Foundations and textbooks

- <a id="codd1970"></a>★ E. F. Codd. "A Relational Model of Data for Large Shared Data Banks." *Communications of the ACM* 13(6):377–387, 1970. [doi:10.1145/362384.362685](https://doi.org/10.1145/362384.362685)  
  *Cited in:* [Chapter 1](01-relational-model.md)
- <a id="codd1972"></a>E. F. Codd. "Further Normalization of the Data Base Relational Model." In R. Rustin (ed.), *Data Base Systems*, Courant Computer Science Symposia 6, Prentice-Hall, 1972.  
  *Cited in:* [Chapter 3](03-types-and-normalization.md)
- <a id="kent1983"></a>W. Kent. "A Simple Guide to Five Normal Forms in Relational Database Theory." *Communications of the ACM* 26(2):120–125, 1983.  
  *Cited in:* [Chapter 3](03-types-and-normalization.md)
- <a id="hellerstein2007"></a>★ J. M. Hellerstein, M. Stonebraker, J. Hamilton. "Architecture of a Database System." *Foundations and Trends in Databases* 1(2):141–259, 2007. [doi:10.1561/1900000002](https://doi.org/10.1561/1900000002)  
  *Cited in:* [Chapter 1](01-relational-model.md)
- <a id="ramakrishnan2003"></a>R. Ramakrishnan, J. Gehrke. *Database Management Systems*, 3rd ed. McGraw-Hill, 2003.  
  *Cited in:* [Chapter 1](01-relational-model.md)
- <a id="silberschatz2019"></a>A. Silberschatz, H. F. Korth, S. Sudarshan. *Database System Concepts*, 7th ed. McGraw-Hill, 2019.  
  *Cited in:* [Chapter 1](01-relational-model.md)
- <a id="petrov2019"></a>A. Petrov. *Database Internals: A Deep Dive into How Distributed Data Systems Work.* O'Reilly, 2019.  
  *Cited in:* [Chapter 5](05-keys-and-indexes.md), [Chapter 15](15-b-trees.md), [Appendix D](appendix-d-answers.md)
- <a id="fowler2002"></a>M. Fowler. *Patterns of Enterprise Application Architecture.* Addison-Wesley, 2002. Pattern summaries online: [Unit of Work](https://martinfowler.com/eaaCatalog/unitOfWork.html), [Identity Map](https://martinfowler.com/eaaCatalog/identityMap.html).  
  *Cited in:* [Chapter 8](08-unit-of-work-i.md), [Chapter 9](09-unit-of-work-ii.md)

## Transactions, isolation and recovery

- <a id="harder1983"></a>T. Härder, A. Reuter. "Principles of Transaction-Oriented Database Recovery." *ACM Computing Surveys* 15(4):287–317, 1983. (The paper that named ACID.)  
  *Cited in:* [Chapter 1](01-relational-model.md), [Chapter 4](04-constraints.md)
- <a id="eswaran1976"></a>K. P. Eswaran, J. N. Gray, R. A. Lorie, I. L. Traiger. "The Notions of Consistency and Predicate Locks in a Database System." *Communications of the ACM* 19(11):624–633, 1976.  
  *Cited in:* [Chapter 12](12-isolation.md)
- <a id="kung1981"></a>★ H. T. Kung, J. T. Robinson. "On Optimistic Methods for Concurrency Control." *ACM Transactions on Database Systems* 6(2):213–226, 1981. [doi:10.1145/319566.319567](https://doi.org/10.1145/319566.319567)  
  *Cited in:* [Chapter 12](12-isolation.md)
- <a id="bernstein1987"></a>P. A. Bernstein, V. Hadzilacos, N. Goodman. *Concurrency Control and Recovery in Database Systems.* Addison-Wesley, 1987. [Free download from Microsoft Research](https://www.microsoft.com/en-us/research/people/philbe/book).  
  *Cited in:* [Chapter 12](12-isolation.md)
- <a id="berenson1995"></a>★ H. Berenson, P. Bernstein, J. Gray, J. Melton, E. O'Neil, P. O'Neil. "A Critique of ANSI SQL Isolation Levels." *Proc. ACM SIGMOD*, 1995.  
  *Cited in:* [Chapter 12](12-isolation.md)
- <a id="mohan1992"></a>C. Mohan, D. Haderle, B. Lindsay, H. Pirahesh, P. Schwarz. "ARIES: A Transaction Recovery Method Supporting Fine-Granularity Locking and Partial Rollbacks Using Write-Ahead Logging." *ACM Transactions on Database Systems* 17(1):94–162, 1992. [doi:10.1145/128765.128770](https://doi.org/10.1145/128765.128770)  
  *Cited in:* [Chapter 8](08-unit-of-work-i.md), [Chapter 13](13-persistence.md), [Chapter 15](15-b-trees.md), [Appendix D](appendix-d-answers.md)
- <a id="pillai2014"></a>T. S. Pillai, V. Chidambaram, R. Alagappan, S. Al-Kiswany, A. C. Arpaci-Dusseau, R. H. Arpaci-Dusseau. "All File Systems Are Not Created Equal: On the Complexity of Crafting Crash-Consistent Applications." *Proc. USENIX OSDI*, 2014.  
  *Cited in:* [Chapter 13](13-persistence.md)
- <a id="ports2012"></a>D. R. K. Ports, K. Grittner. "Serializable Snapshot Isolation in PostgreSQL." *Proceedings of the VLDB Endowment* 5(12):1850–1861, 2012.  
  *Cited in:* [Appendix D](appendix-d-answers.md)

## Concurrency and synchronization

- <a id="courtois1971"></a>★ P. J. Courtois, F. Heymans, D. L. Parnas. "Concurrent Control with 'Readers' and 'Writers'." *Communications of the ACM* 14(10):667–668, 1971.  
  *Cited in:* [Chapter 11](11-readers-writer-locks.md)
- <a id="hoare1974"></a>C. A. R. Hoare. "Monitors: An Operating System Structuring Concept." *Communications of the ACM* 17(10):549–557, 1974.  
  *Cited in:* [Chapter 11](11-readers-writer-locks.md)
- <a id="lamport1974"></a>L. Lamport. "A New Solution of Dijkstra's Concurrent Programming Problem." *Communications of the ACM* 17(8):453–455, 1974. (The bakery algorithm.)  
  *Cited in:* [Chapter 11](11-readers-writer-locks.md)
- <a id="mellorcrummey1991"></a>J. M. Mellor-Crummey, M. L. Scott. "Algorithms for Scalable Synchronization on Shared-Memory Multiprocessors." *ACM Transactions on Computer Systems* 9(1):21–65, 1991.  
  *Cited in:* [Chapter 11](11-readers-writer-locks.md)
- <a id="graefe2010"></a>G. Graefe. "A Survey of B-Tree Locking Techniques." *ACM Transactions on Database Systems* 35(3), 2010.  
  *Cited in:* [Chapter 10](10-concurrency-i.md), [Chapter 15](15-b-trees.md)
- <a id="pep703"></a>S. Gross. *PEP 703 – Making the Global Interpreter Lock Optional in CPython.* 2023. <https://peps.python.org/pep-0703/>  
  *Cited in:* [Chapter 10](10-concurrency-i.md)
- <a id="pep779"></a>T. Wouters, M. Page, S. Gross. *PEP 779 – Criteria for supported status for free-threaded Python.* 2025. <https://peps.python.org/pep-0779/>  
  *Cited in:* [Chapter 10](10-concurrency-i.md)
- <a id="brandenburg2009"></a>B. B. Brandenburg, J. H. Anderson. "Reader-Writer Synchronization for Shared-Memory Multiprocessor Real-Time Systems." *Proc. Euromicro Conference on Real-Time Systems (ECRTS)*, 184–193, 2009. (Phase-fair locks.)  
  *Cited in:* [Appendix D](appendix-d-answers.md)

## Query processing and optimization

- <a id="selinger1979"></a>★ P. G. Selinger, M. M. Astrahan, D. D. Chamberlin, R. A. Lorie, T. G. Price. "Access Path Selection in a Relational Database Management System." *Proc. ACM SIGMOD*, 1979. [doi:10.1145/582095.582099](https://doi.org/10.1145/582095.582099)  
  *Cited in:* [Chapter 14](14-query-planning.md)
- <a id="graefe1994"></a>G. Graefe. "Volcano — An Extensible and Parallel Query Evaluation System." *IEEE Transactions on Knowledge and Data Engineering* 6(1):120–135, 1994.  
  *Cited in:* [Chapter 7](07-query-primitives.md)
- <a id="ioannidis1996"></a>Y. E. Ioannidis. "Query Optimization." *ACM Computing Surveys* 28(1):121–123, 1996.  
  *Cited in:* [Chapter 14](14-query-planning.md)

## Storage and indexing

- <a id="bayer1972"></a>R. Bayer, E. McCreight. "Organization and Maintenance of Large Ordered Indexes." *Acta Informatica* 1(3):173–189, 1972.  
  *Cited in:* [Chapter 15](15-b-trees.md)
- <a id="comer1979"></a>★ D. Comer. "The Ubiquitous B-Tree." *ACM Computing Surveys* 11(2):121–137, 1979.  
  *Cited in:* [Chapter 15](15-b-trees.md)
- <a id="graefe2011"></a>G. Graefe. "Modern B-Tree Techniques." *Foundations and Trends in Databases* 3(4):203–402, 2011.  
  *Cited in:* [Chapter 15](15-b-trees.md)
- <a id="oneil1996"></a>P. O'Neil, E. Cheng, D. Gawlick, E. O'Neil. "The Log-Structured Merge-Tree (LSM-Tree)." *Acta Informatica* 33(4):351–385, 1996.  
  *Cited in:* [Chapter 15](15-b-trees.md)

## Parsing

- <a id="pratt1973"></a>V. R. Pratt. "Top Down Operator Precedence." *Proc. ACM Symposium on Principles of Programming Languages (POPL)*, 1973.  
  *Cited in:* [Appendix A](appendix-a-sql-parser.md)
- <a id="nystrom2021"></a>R. Nystrom. *Crafting Interpreters.* Genever Benning, 2021. Free online: <https://craftinginterpreters.com/>  
  *Cited in:* [Appendix A](appendix-a-sql-parser.md)

## Online documentation

- <a id="sqlite-rowid"></a>SQLite. "Rowid Tables." <https://www.sqlite.org/rowidtable.html>  
  *Cited in:* [Chapter 1](01-relational-model.md), [Chapter 2](02-tables-and-crud.md)
- <a id="sqlite-types"></a>SQLite. "Datatypes In SQLite" (type affinity). <https://www.sqlite.org/datatype3.html>  
  *Cited in:* [Chapter 3](03-types-and-normalization.md)
- <a id="sqlite-transactions"></a>SQLite. "Transaction" (`BEGIN DEFERRED`, `IMMEDIATE`, `EXCLUSIVE`). <https://www.sqlite.org/lang_transaction.html>  
  *Cited in:* [Chapter 11](11-readers-writer-locks.md)
- <a id="sqlite-atomic"></a>SQLite. "Atomic Commit In SQLite." <https://www.sqlite.org/atomiccommit.html>  
  *Cited in:* [Chapter 13](13-persistence.md)
- <a id="sqlite-lang"></a>SQLite. "SQL As Understood By SQLite." <https://www.sqlite.org/lang.html>  
  *Cited in:* [Appendix A](appendix-a-sql-parser.md)
- <a id="uax15"></a>Unicode Consortium. *Unicode Standard Annex #15: Unicode Normalization Forms.* <https://unicode.org/reports/tr15/>  
  *Cited in:* [Chapter 3](03-types-and-normalization.md)
- <a id="sqlalchemy"></a>SQLAlchemy. "Session Basics" and "Unit of Work" (ORM documentation). <https://docs.sqlalchemy.org/en/20/orm/session_basics.html>  
  *Cited in:* [Appendix D](appendix-d-answers.md)

---

[🏠 Contents](index.md)
