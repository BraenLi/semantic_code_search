// C++ utility classes for data processing

#include <string>
#include <vector>
#include <memory>

namespace utils {

class DataProcessor {
public:
    virtual void process(const std::string& input) = 0;
    virtual ~DataProcessor() = default;
};

class JsonProcessor : public DataProcessor {
private:
    std::string schema;
    
public:
    JsonProcessor(const std::string& s) : schema(s) {}
    
    void process(const std::string& input) override {
        // Parse and validate JSON against schema
        if (input.empty()) return;
        // JSON processing logic here
    }
    
    std::string getSchema() const { return schema; }
};

class CsvProcessor : public DataProcessor {
private:
    char delimiter;
    
public:
    CsvProcessor(char delim = ',') : delimiter(delim) {}
    
    void process(const std::string& input) override {
        // Parse CSV data
        std::vector<std::string> fields;
        // CSV parsing logic here
    }
};

std::shared_ptr<DataProcessor> createProcessor(const std::string& type) {
    if (type == "json") {
        return std::make_shared<JsonProcessor>("default");
    } else if (type == "csv") {
        return std::make_shared<CsvProcessor>(',');
    }
    return nullptr;
}

} // namespace utils
